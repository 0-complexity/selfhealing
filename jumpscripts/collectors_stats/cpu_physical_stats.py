from JumpScale import j
import re


descr = """
Gathers following CPU statistics from physical machines:
- CPU time
- CPU percent
- Number of threads
- Number of context switches
- Number of interrupts

Statistics are writen to Redis.
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
queue = "process"
log = False

roles = ["node"]


def action():
    if j.system.platformtype.isVirtual():
        return
    import psutil

    rediscl = j.clients.redis.getByInstance("system")
    aggregatorcl = j.tools.aggregator.getClient(
        rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    )

    results = {}
    # CPU Time
    cpu_times = psutil.cpu_times(percpu=True)
    now = j.base.time.getTimeEpoch()
    for cpu_nr, cpu_time in enumerate(cpu_times):
        value = int(cpu_time.user + cpu_time.system)
        key = "machine.CPU.utilisation@phys.%d.%d.%d" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            cpu_nr,
        )
        tags = "gid:%d nid:%d cpu_nr:%s type:physical" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            cpu_nr,
        )
        aggregatorcl.measureDiff(key, tags, value, timestamp=now)
        results[key] = value

    # CPU percent
    cpu_percent = psutil.cpu_percent(percpu=True)
    now = j.base.time.getTimeEpoch()
    for cpu_nr, cpu_percent in enumerate(cpu_percent):
        key = "machine.CPU.percent@phys.%d.%d.%d" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            cpu_nr,
        )
        tags = "gid:%d nid:%d cpu_nr:%s type:physical" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            cpu_nr,
        )
        aggregatorcl.measure(key, tags, cpu_percent, timestamp=now)
        results[key] = value

    # Number of threads
    total = 0
    for proc in psutil.process_iter():
        try:
            total += proc.num_threads()
        except psutil.NoSuchProcess:
            pass

    key = "machine.process.threads@phys.%d.%d" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    tags = "gid:%d nid:%d type:physical" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    aggregatorcl.measure(key, tags, total, timestamp=now)
    results[key] = total

    stat = j.system.fs.fileGetContents("/proc/stat")
    stats = dict()
    for line in stat.splitlines():
        _, key, value = re.split("^(\w+)\s", line)
        stats[key] = value

    # Number of contextswitch
    key = "machine.CPU.contextswitch@phys.%d.%d" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    value = int(stats["ctxt"])
    tags = "gid:%d nid:%d type:physical" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    aggregatorcl.measureDiff(key, tags, value, timestamp=now)
    results[key] = value

    # Number of interrupts
    key = "machine.CPU.interrupts@phys.%d.%d" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    value = int(stats["intr"].split(" ")[0])
    tags = "gid:%d nid:%d type:physical" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    aggregatorcl.measureDiff(key, tags, value, timestamp=now)
    results[key] = value

    return results


if __name__ == "__main__":
    results = action()
    import yaml

    print yaml.dump(results)
