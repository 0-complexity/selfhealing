from JumpScale import j
import json
import sys

descr = """
Gathers statistics about the vPools.
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


def pop_realtime_info(points):
    pop_points = [k for (k, v) in points.iteritems() if k.endswith("_ps")]

    for point in pop_points:
        points.pop(point, None)

    return points


def format_tags(tags):
    out = ''
    for k, v in tags.iteritems():
        out += "%s:%s " % (k, v)
    return out.strip()


def action():
    """
    Send VPools statistics to DB
    """
    sys.path.append('/opt/OpenvStorage')
    from ovs.dal.lists.vpoollist import VPoolList

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    vpools = VPoolList.get_vpools()
    if len(vpools) == 0:
        return

    for vpool in vpools:
        metrics = pop_realtime_info(vpool.statistics)
        now = j.base.time.getTimeEpoch()

        str_metrics = json.dumps(metrics)
        metrics = json.loads(str_metrics, parse_int=float)
        vpool_name = vpool.name

        for key, value in metrics.iteritems():
            key = "ovs.vpool.%s@%s" % (key, vpool_name)
            tags = {
                'gid': j.application.whoAmI.gid,
                'nid': j.application.whoAmI.nid,
                'vpool_name': vpool_name,
            }
            aggregatorcl.measureDiff(key, format_tags(tags), value, timestamp=now)

        all_results[vpool_name] = metrics

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
