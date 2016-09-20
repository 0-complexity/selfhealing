from JumpScale import j
import sys

descr = """
gather statistics about OVS ASD
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

roles = ['storagedriver']


def format_tags(tags):
    out = ''
    for k, v in tags.iteritems():
        out += "%s:%s " % (k, v)
    return out.strip()


def action():
    """
    Send OVS asd statistics to DB
    """
    sys.path.append('/opt/OpenvStorage')
    from ovs.dal.hybrids.albabackend import AlbaBackend
    from ovs.dal.lists.albabackendlist import AlbaBackendList
    from ovs.extensions.generic.system import System

    if System.get_my_storagerouter().node_type != 'MASTER':
        return {}

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    abl = AlbaBackendList.get_albabackends()
    for ab in abl:
        for asd, result in ab.asd_statistics.iteritems():
            now = j.base.time.getTimeEpoch()
            result = {
                'capacity': float(result['capacity']),
                'creation': float(result['creation']),
                'disk_usage': float(result['disk_usage']),
                'period': float(result['period']),
                'apply': float(result['Apply']['n']),
                'getdiskusage': float(result['GetDiskUsage']['n']),
                'multiget2': float(result['MultiGet2']['n']),
                'range': float(result['Range']['n']),
                'statistics': float(result['Statistics']['n'])
            }

            for key, value in result.iteritems():
                key = "ovs.asd.%s@%s" % (key, ab.alba_id)
                tags = {
                    'gid': j.application.whoAmI.gid,
                    'nid': j.application.whoAmI.nid,
                    'backend_name': ab.name,
                    'alba_id': ab.alba_id,
                    'long_id': asd,
                }
                aggregatorcl.measureDiff(key, format_tags(tags), value, timestamp=now)

            all_results[ab.alba_id] = result

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
