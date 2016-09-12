from JumpScale import j
import sys

descr = """
gather statistics about disk safety
Send disk safety for each vpool and the amount of namespaces with the lowest disk safety to DB
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


def action():
    """
    Send disk safety for each vpool and the amount of namespaces with the lowest disk safety to DB
    """
    sys.path.append('/opt/OpenvStorage')
    from ovs.dal.lists.servicelist import ServiceList
    from ovs.dal.hybrids.service import Service
    from ovs.dal.hybrids.servicetype import ServiceType
    from ovs.dal.lists.albabackendlist import AlbaBackendList
    from ovs.extensions.plugins.albacli import AlbaCLI
    from ovs.extensions.generic.system import System

    if System.get_my_storagerouter().node_type != 'MASTER':
        return {}

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {
        'disk_lost': {},
        'disk_safety': {},
        'bucket': {},
    }

    points = []
    abms = []

    for service in ServiceList.get_services():
        if service.type.name == ServiceType.SERVICE_TYPES.ALBA_MGR:
            abms.append(service.name)

    abms = list(set(abms))
    abl = AlbaBackendList.get_albabackends()
    for ab in abl:
        service_name = Service(ab.abm_services[0].service_guid).name
        if service_name not in abms:
            continue

        config = "etcd://127.0.0.1:2379/ovs/arakoon/{}/config".format(service_name)

        try:
            namespaces = AlbaCLI.run('show-namespaces', config=config, to_json=True)[1]
        except Exception as ex:
            continue

        now = j.base.time.getTimeEpoch()

        disk_lost_overview = {}
        disk_safety_overview = {}
        bucket_overview = {}
        total_objects = 0
        for namespace in namespaces:
            statistics = namespace['statistics']
            bucket_counts = statistics['bucket_count']
            for bucket_count in bucket_counts:
                bucket, objects = bucket_count
                total_objects += objects
                disk_lost = bucket[0] + bucket[1] - bucket[2]
                disk_safety = bucket[1] - disk_lost
                if str(bucket) not in bucket_overview:
                    bucket_overview[str(bucket)] = {'objects': 0, 'disk_safety': 0}
                if disk_lost not in disk_lost_overview:
                    disk_lost_overview[disk_lost] = 0
                if disk_safety not in disk_safety_overview:
                    disk_safety_overview[disk_safety] = 0
                disk_lost_overview[disk_lost] += objects
                disk_safety_overview[disk_safety] += objects
                bucket_overview[str(bucket)]['objects'] += objects
                bucket_overview[str(bucket)]['disk_safety'] = disk_safety

        for disk_lost, objects in disk_lost_overview.iteritems():
            tags = {
                'backend_name': ab.name,
                'disk_lost': disk_lost,
                'gid': j.application.whoAmI.gid,
                'nid': j.application.whoAmI.nid,
            }
            result = {
                'total_objects': total_objects,
                'objects': objects
            }
            for k, value in result.iteritems():
                key = 'ovs.disk_lost.%s@%s.%s' % (k, ab.name, disk_lost)
                aggregatorcl.measure(key, format_tags(tags), value, timestamp=now)

            all_results['disk_lost']["%s.%s" % (ab.name, disk_lost)] = result

        for disk_safety, objects in disk_safety_overview.iteritems():
            tags = {
                'backend_name': ab.name,
                'disk_safety': disk_safety,
                'gid': j.application.whoAmI.gid,
                'nid': j.application.whoAmI.nid,
            }
            result = {
                'total_objects': total_objects,
                'objects': objects
            }
            for k, value in result.iteritems():
                key = 'ovs.disk_safety.%s@%s.%s' % (k, ab.name, disk_safety)
                aggregatorcl.measure(key, format_tags(tags), value, timestamp=now)

            all_results['disk_safety']["%s.%s" % (ab.name, disk_safety)] = result

        for bucket_count, values in bucket_overview.iteritems():
            tags = {
                'backend_name': ab.name,
                'bucket': bucket_count,
                'disk_safety': disk_safety,
                'gid': j.application.whoAmI.gid,
                'nid': j.application.whoAmI.nid,
                'disk_safety': values['disk_safety']
            }
            result = {
                'total_objects': total_objects,
                'objects': result['objects']
            }
            for k, value in result.iteritems():
                key = 'ovs.bucket.%s@%s.%s' % (k, ab.name, bucket_count)
                aggregatorcl.measure(key, format_tags(tags), value, timestamp=now)

            all_results['bucket']["%s.%s" % (ab.name, bucket_count)] = result

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
