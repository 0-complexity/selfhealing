from JumpScale import j
import sys

descr = """
Gather statistics about Open vStorage ASD.
"""

organization = "greenitglobe"
author = "christophe@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "disk.monitoring"
timeout = 60
order = 1
enable = False
async = True
queue = 'process'
log = False

roles = ['storagemaster']


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
    from ovs.dal.lists.albabackendlist import AlbaBackendList

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    abl = AlbaBackendList.get_albabackends()
    for ab in abl:
        for asd, result in ab.asd_statistics.iteritems():
            now = j.base.time.getTimeEpoch()
            measurement_key = "%s/%s" % (ab.alba_id, asd)
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
                key = "ovs.asd.%s@%s" % (key, measurement_key)
                tags = {
                    'gid': j.application.whoAmI.gid,
                    'nid': j.application.whoAmI.nid,
                    'backend_name': ab.name,
                    'alba_id': ab.alba_id,
                    'long_id': asd,
                }
                aggregatorcl.measureDiff(key, format_tags(tags), value, timestamp=now)

            all_results[measurement_key] = result

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
