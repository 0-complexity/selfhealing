from JumpScale import j
import sys

descr = """
gather statistics about OVS proxy performance
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "disk.monitoring"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
queue = 'process'
log = False

roles = ['storagerouter']


def format_tags(tags):
    out = ''
    for k, v in tags.iteritems():
        out += "%s:%s " % (k, v)
    return out.strip()


def get_backends_and_proxy_ports(hostname):
    sr = StorageRouterList.get_by_name(hostname)
    st = ServiceTypeList.get_by_name(ServiceType.SERVICE_TYPES.ALBA_PROXY)
    proxies = {}
    for service in st.services:
        if service.storagerouter_guid == sr.guid:
            for storagedriver in sr.storagedrivers:
                vpool = storagedriver.vpool
                proxies[vpool.name] = {
                    'port': service.ports[0],
                    'ip': storagedriver.storage_ip,
                    'backend_name': vpool.metadata['backend']['name']
                }
    return proxies


def get_stats_from_proxy(hostname, vpoolname, ip, port, backendname, aggregatorcl):
    try:
        output = AlbaCLI.run(command='proxy-statistics', host=ip, port=port, to_json=True)['ns_stats']
    except Exception:
        raise Exception("Could not get statistics from proxy at {0}:{1}".format(ip, port))

    now = j.base.time.getTimeEpoch()

    proxy_id = "%s.%s.%s" % (hostname, vpoolname, backendname)
    tags = {
        'server': hostname,
        'vpool_name': vpoolname,
        'backend_name': backendname
    }
    fields = {
        'download_totaltime': 0.0,
        'download_exp_totaltime': 0.0,
        'download_avg': 0.0,
        'download_exp_avg': 0.0,
        'download_number': 0.0,
        'upload_totaltime': 0.0,
        'upload_exp_totaltime': 0.0,
        'upload_avg': 0.0,
        'upload_exp_avg': 0.0,
        'upload_number': 0.0,
        'partial_read_time_totaltime': 0.0,
        'partial_read_time_exp_totaltime': 0.0,
        'partial_read_time_avg': 0.0,
        'partial_read_time_exp_avg': 0.0,
        'partial_read_time_number': 0.0,
        'partial_read_size_totaltime': 0.0,
        'partial_read_size_exp_totaltime': 0.0,
        'partial_read_size_avg': 0.0,
        'partial_read_size_exp_avg': 0.0,
        'partial_read_size_number': 0.0,
        'fragment_cache_hits': 0.0,
        'fragment_cache_misses': 0.0,
        'manifest_cached': 0.0,
        'manifest_from_nsm': 0.0,
        'manifest_stale': 0.0
    }

    if len(output) == 0:
        return fields

    try:
        for namespace in output:
            stats = namespace[1]

            for key in ['download', 'upload', 'partial_read_time', 'partial_read_size']:
                stats_key = stats[key]
                fields['%s_avg' % key] += float(stats_key['avg'])
                fields['%s_exp_avg' % key] += float(stats_key['exp_avg'])
                fields['%s_totaltime' % key] += float(stats_key['avg']) * int(stats_key['n'])
                fields['%s_exp_totaltime' % key] += float(stats_key['exp_avg']) * int(stats_key['n'])
                fields['%s_number' % key] += float(stats_key['n'])
            fields['fragment_cache_hits'] += float(stats['fragment_cache_hits'])
            fields['fragment_cache_misses'] += float(stats['fragment_cache_misses'])
            fields['manifest_cached'] += float(stats['manifest_cached'])
            fields['manifest_from_nsm'] += float(stats['manifest_from_nsm'])
            fields['manifest_stale'] += float(stats['manifest_stale'])

        keys = ('avg', 'totaltime')

        for key, value in fields.iteritems():
            if key.endswith(keys):
                fields[key] = float(fields[key] / len(output))

        for key, value in fields.iteritems():
            key = "ovs.proxy.%s@%s" % (key, proxy_id)
            aggregatorcl.measure(key, format_tags(tags), value, timestamp=now)
    except Exception:
        raise

    return (proxy_id, fields)


def action():
    """
    Send OVS proxy performance statistics to DB
    """
    sys.path.append('/opt/OpenvStorage')
    from ovs.extensions.plugins.albacli import AlbaCLI
    from ovs.dal.lists.servicetypelist import ServiceTypeList
    from ovs.dal.hybrids.servicetype import ServiceType
    from ovs.dal.lists.storagerouterlist import StorageRouterList

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    _, out = j.system.process.execute('hostname -s')
    hostname = out.strip()
    proxies = get_backends_and_proxy_ports(hostname.strip())

    for vpool, services in proxies.iteritems():
        proxy_id, result = get_stats_from_proxy(hostname, vpool, services['ip'],
                                                services['port'],
                                                services['backend_name'],
                                                aggregatorcl)
        all_results[proxy_id] = result

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
