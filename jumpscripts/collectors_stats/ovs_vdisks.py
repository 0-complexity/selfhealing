from JumpScale import j
import json
import sys

descr = """
gather statistics about VDisks
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
    Send vdisks statistics to DB
    """
    sys.path.append('/opt/OpenvStorage')
    from ovs.dal.lists.vdisklist import VDiskList
    from ovs.dal.hybrids.vpool import VPool
    from ovs.dal.hybrids.storagerouter import StorageRouter
    from ovs.extensions.generic.system import System

    if System.get_my_storagerouter().node_type != 'MASTER':
        return {}

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    vdisks = VDiskList.get_vdisks()
    if len(vdisks) == 0:
        return all_results

    points = []

    for vdisk in vdisks:

        metrics = pop_realtime_info(vdisk.statistics)
        now = j.base.time.getTimeEpoch()

        volume_id = vdisk.volume_id
        disk_name = vdisk.name
        failover_mode = vdisk.info.get('failover_mode')

        if failover_mode in ['OK_STANDALONE', 'OK_SYNC']:
            failover_status = 0
        elif failover_mode == 'CATCHUP':
            failover_status = 1
        elif failover_mode == 'DEGRADED':
            failover_status = 2
        else:
            failover_status = 3

        metrics['failover_mode_status'] = failover_status

        str_metrics = json.dumps(metrics)
        metrics = json.loads(str_metrics, parse_int=float)

        vpool_name = VPool(vdisk.vpool_guid).name

        for key, value in metrics.iteritems():
            stat_key = "ovs.vdisk.%s@%s" % (key, volume_id)
            tags = {
                'gid': j.application.whoAmI.gid,
                'nid': j.application.whoAmI.nid,
                'disk_name': disk_name,
                'volume_id': volume_id,
                'storagerouter_name': StorageRouter(vdisk.storagerouter_guid).name,
                'vpool_name': vpool_name,
                'failover_mode': vdisk.info['failover_mode']
            }
            if key == 'failover_mode_status':
                aggregatorcl.measure(stat_key, format_tags(tags), value, timestamp=now)
            else:
                aggregatorcl.measureDiff(stat_key, format_tags(tags), value, timestamp=now)

        all_results[volume_id] = metrics

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
