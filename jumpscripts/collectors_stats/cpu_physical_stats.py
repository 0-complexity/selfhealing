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
    cpu_times = psutil.cpu_times(percpu=True)
    now = j.base.time.getTimeEpoch()
    for cpu_nbr, cpu_time in enumerate(cpu_times):
        results['machine.CPU.utilisation.phys.%d.%d.%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid, cpu_nbr)] = int(cpu_time.user + cpu_time.system)

    stat = j.system.fs.fileGetContents('/proc/stat')
    stats = dict()
    for line in stat.splitlines():
        _, key, value = re.split("^(\w+)\s", line)
        stats[key] = value

    results["machine.CPU.contextswitch"] = int(stats['ctxt'])

    for key, value in results.iteritems():
        tags = 'gid:%d nid:%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)
        aggregatorcl.measure(key, tags, value, timestamp=now)

    return results

if __name__ == '__main__':
    results = action()
    import yaml
    print yaml.dump(results)
