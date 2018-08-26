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
    Send VPools statistics to DB
    """
    sys.path.append("/opt/OpenvStorage")
    from ovs.dal.lists.vpoollist import VPoolList

    rediscl = j.clients.redis.getByInstance("system")
    aggregatorcl = j.tools.aggregator.getClient(
        rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    )

    vpools = VPoolList.get_vpools()
    if len(vpools) == 0:
        return

    for vpool in vpools:
        metrics = vpool.statistics
        now = j.base.time.getTimeEpoch()

        str_metrics = json.dumps(metrics)
        metrics = json.loads(str_metrics, parse_int=float)
        vpool_name = vpool.name

        for key, value in metrics.iteritems():
            if key.endswith("_ps") or not isinstance(value, float):
                continue
            key = "ovs.vpool.%s@%s" % (key, vpool_name)
            tags = {
                "gid": j.application.whoAmI.gid,
                "nid": j.application.whoAmI.nid,
                "vpool_name": vpool_name,
            }
            aggregatorcl.measureDiff(key, format_tags(tags), value, timestamp=now)


if __name__ == "__main__":
    action()
