from JumpScale import j
import time
import json
from ovs.dal.lists.vpoollist import VPoolList

descr = """
gather statistics about VPools
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


def amIMaster():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    ocl = j.clients.osis.getByInstance('main')
    nodecl = j.clients.osis.getCategory(ocl, 'system', 'node')

    nodes = nodecl.search({'roles': 'storagedriver'})[1:]
    nodes = sorted(nodes, key=lambda k: k['id'])

    if nodes[0]['gid'] != gid or nodes[0]['id'] != nid:
        return False

    return True


def action():
    """
    Send VPools statistics to DB
    """
    if not amIMaster():
        return {}

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    vpools = VPoolList.get_vpools()
    if len(vpools) == 0:
        StatsmonkeyController._logger.info("No vpools found")
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
            aggregatorcl.measure(key, format_tags(tags), value, timestamp=now)

        all_results[vpool_name] = metrics

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
