from JumpScale import j
import re


descr = """
Gathers statistics about the memory of the physical machines.
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


def get_swap_cached():
    import re

    info = j.system.fs.fileGetTextContents('/proc/meminfo')
    m = re.search('^SwapCached:\s*(\d+)', info, re.M)
    return int(m.group(1)) * 1024


def action():
    if j.system.platformtype.isVirtual():
        return
    import psutil
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    results = {}
    memory = psutil.virtual_memory()
    now = j.base.time.getTimeEpoch()
    results['machine.memory.ram.available'] = round(memory.available / (1024.0 * 1024.0), 2)

    swap = psutil.swap_memory()
    cached = get_swap_cached()
    free = swap.free + cached
    results["machine.memory.swap.left"] = round(free / (1024.0 * 1024.0), 2)
    used = swap.used - cached
    results["machine.memory.swap.used"] = round(used / (1024.0 * 1024.0), 2)

    for key, value in results.iteritems():
        key = "%s@phys.%d.%d" % (key, j.application.whoAmI.gid, j.application.whoAmI.nid)
        tags = 'gid:%d nid:%d type:physical' % (j.application.whoAmI.gid, j.application.whoAmI.nid)
        aggregatorcl.measure(key, tags, value, timestamp=now)

    return results


if __name__ == '__main__':
    results = action()
    import yaml
    print yaml.dump(results)
