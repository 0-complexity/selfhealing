from JumpScale import j
import JumpScale.baselib.redis

descr = """
Monitors the workers, checking if they report back on regular basis report to their agent for new tasks.

Throws ERROR if WORKERS waits longer than expected:
For Default queue > 2 mins
For IO queue > 2 hours
For Hypervisor queue > 10 mins
For Process queue > 1 min
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"
async = True
roles = ["node"]
queue = "process"
period = 600
log = True
timeout = 60


def action():
    rediscl = j.clients.redis.getByInstance("system")
    timemap = {"default": "-2m", "io": "-2h", "hypervisor": "-10m", "process": "-1m"}
    results = list()

    for queue in ("io", "hypervisor", "default", "process"):
        result = {"category": "Workers"}
        lastactive = float(rediscl.hget("workers:heartbeat", queue) or 0)
        timeout = timemap.get(queue)
        lastactiv = "{{ts:%s}}" % lastactive if lastactive else "never"
        result["message"] = "*%s last active*: %s" % (queue.upper(), lastactiv)
        if j.base.time.getEpochAgo(timeout) < lastactive:
            result["state"] = "OK"
        else:
            j.errorconditionhandler.raiseOperationalCritical(
                result["message"], "monitoring", die=False
            )
            result["state"] = "ERROR"
            result["uid"] = "queue:{}".format(queue.upper())

        results.append(result)
    return results


if __name__ == "__main__":
    print action()
