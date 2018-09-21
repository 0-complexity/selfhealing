from JumpScale import j
import json
import sys

descr = """
Gathers statistics about the virtual disks.
"""

organization = "greenitglobe"
author = "christophe@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "disk.monitoring"
timeout = 60
order = 1
enable = True
async = True
queue = "process"
log = False

roles = ["storagemaster"]


def format_tags(tags):
    out = ""
    for k, v in tags.iteritems():
        out += "%s:%s " % (k, v)
    return out.strip()


def action():
    """
    Send vdisks statistics to DB
    """
    sys.path.append("/opt/OpenvStorage")
    from ovs.dal.lists.vdisklist import VDiskList
    from ovs.dal.hybrids.vpool import VPool
    from ovs.dal.hybrids.storagerouter import StorageRouter

    rediscl = j.clients.redis.getByInstance("system")
    aggregatorcl = j.tools.aggregator.getClient(
        rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    )

    all_results = {}

    vdisks = VDiskList.get_vdisks()
    if len(vdisks) == 0:
        return all_results

    vpools = dict()
    storage_routers = dict()

    for vdisk in vdisks:

        metrics = vdisk.statistics
        now = j.base.time.getTimeEpoch()

        volume_id = vdisk.volume_id
        if volume_id is None:
            continue

        disk_name = vdisk.name
        failover_mode = vdisk.info.get("failover_mode")

        if failover_mode in ["OK_STANDALONE", "OK_SYNC"]:
            failover_status = 0
        elif failover_mode == "CATCHUP":
            failover_status = 1
        elif failover_mode == "DEGRADED":
            failover_status = 2
        else:
            failover_status = 3

        metrics["failover_mode_status"] = failover_status

        str_metrics = json.dumps(metrics)
        metrics = json.loads(str_metrics, parse_int=float)

        vpool_name = vpools.get(vdisk.vpool_guid)
        if vpool_name is None:
            vpool_name = VPool(vdisk.vpool_guid).name
            vpools[vdisk.vpool_guid] = vpool_name

        storage_router_name = storage_routers.get(vdisk.storagerouter_guid)
        if storage_router_name is None:
            storage_router_name = StorageRouter(vdisk.storagerouter_guid).name
            storage_routers[vdisk.storagerouter_guid] = storage_router_name

        for key, value in metrics.iteritems():
            if key.endswith("_ps") or not isinstance(value, float):
                continue
            stat_key = "ovs.vdisk.%s@%s" % (key, volume_id)
            tags = {
                "gid": j.application.whoAmI.gid,
                "nid": j.application.whoAmI.nid,
                "disk_name": disk_name,
                "volume_id": volume_id,
                "storagerouter_name": storage_router_name,
                "vpool_name": vpool_name,
                "failover_mode": vdisk.info["failover_mode"],
            }
            if key == "failover_mode_status":
                aggregatorcl.measure(stat_key, format_tags(tags), value, timestamp=now)
            else:
                aggregatorcl.measureDiff(
                    stat_key, format_tags(tags), value, timestamp=now
                )


if __name__ == "__main__":
    action()
