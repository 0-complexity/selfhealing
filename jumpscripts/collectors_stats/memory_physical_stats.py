from JumpScale import j
import re


descr = """
gather statistics about system
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitoring.processes"
period = 60  # always in sec
timeout = period * 0.2
enable = True
async = True
queue = 'process'
log = False

roles = []


def action():
    import psutil
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    results = {}
    memory = psutil.virtual_memory()
    now = j.base.time.getTimeEpoch()
    results['machine.memory.ram.available'] = round(memory.available / (1024.0 * 1024.0), 2)

    swap = psutil.swap_memory()
    results["machine.memory.swap.left"] = round(swap.free / (1024.0 * 1024.0), 2)
    results["machine.memory.swap.used"] = round(swap.used / (1024.0 * 1024.0), 2)

    for key, value in results.iteritems():
        key = "%s_%d_%d" % (key, j.application.whoAmI.gid, j.application.whoAmI.nid)
        tags = 'gid:%d nid:%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)
        aggregatorcl.measure(key, tags, value, timestamp=now)

    return results

if __name__ == '__main__':
    results = action()
    import yaml
    print yaml.dump(results)
