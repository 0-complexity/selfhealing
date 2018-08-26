from JumpScale import j
import time
import re
import os

descr = """
Gathers following statistics about specific processes:
- VmRSS
- VmSize
"""

organization = "jumpscale"
author = "geert@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "process.monitoring"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
queue = "process"
log = False

roles = ["node"]

NAMEFINDER = dict(
    volumedriver_fs=[[re.compile(r"^/mnt/(\w+)$")]],
    arakoon=[
        [re.compile("^arakoon://config/ovs/arakoon/(.+?)/config.*$")],
        [re.compile("^/opt/(OpenvStorage)/config/arakoon_config\\.ini$")],
    ],
    alba=[
        [
            re.compile("^(asd\\-start)$"),
            re.compile("^arakoon://config/ovs/alba/asds/(.*?)\\?.*$"),
        ],
        [
            re.compile("^(proxy\\-start)$"),
            re.compile("^arakoon://config/ovs/vpools/(.*?)\\?.*$"),
        ],
    ],
)


def action():
    if j.system.platformtype.isVirtual():
        return
    import psutil

    rediscl = j.clients.redis.getByInstance("system")
    aggregatorcl = j.tools.aggregator.getClient(
        rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    )

    now = j.base.time.getTimeEpoch()
    results = {}

    for process in psutil.process_iter():
        try:
            cmdline = process.cmdline()
            memory_info = process.memory_info()
        except psutil.NoSuchProcess:
            continue
        if not cmdline:
            continue
        executable = cmdline[0].split(os.path.sep)[-1]
        if executable not in ("arakoon", "alba", "volumedriver_fs"):
            continue
        for regexes in NAMEFINDER[executable]:
            tags = list()
            all_match = True
            for regex in regexes:
                match = False
                for part in cmdline:
                    m = regex.match(part)
                    if m:
                        tags.append(m.group(1))
                        match = True
                        break
                if not match:
                    all_match = False
                    break
            if all_match:
                executable = "_".join([executable] + tags)
                break

        # VmRSS
        value = memory_info.rss
        key = "process.memory.vmrss@phys.%d.%d.%s" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            executable,
        )
        tags = "gid:%d nid:%d process:%s type:physical" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            executable,
        )
        aggregatorcl.measure(key, tags, value, timestamp=now)
        results[key] = value

        # VmSize
        value = memory_info.vms
        key = "process.memory.vmsize@phys.%d.%d.%s" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            executable,
        )
        tags = "gid:%d nid:%d process:%s type:physical" % (
            j.application.whoAmI.gid,
            j.application.whoAmI.nid,
            executable,
        )
        aggregatorcl.measure(key, tags, value, timestamp=now)
        results[key] = value

    return results


if __name__ == "__main__":
    results = action()
    import yaml

    print(yaml.dump(results))
