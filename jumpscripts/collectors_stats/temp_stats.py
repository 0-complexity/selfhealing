from JumpScale import j

descr = """
Checks the temperature on the system.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitoring.processes"
roles = ['node']
period = 60  # 1min
enable = True
async = True
queue = 'process'
log = True


def action():
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))
    gid, nid = j.application.whoAmI.gid, j.application.whoAmI.nid
    labeled = sorted(glob.glob("/sys/class/hwmon/*/temp*_label")
    for f in labeled:
        label = open(f).read() #Core 0
        if "core" not in label.lower():
            continue
        coreid = int(label.split()[1])
        inputtemp = int(open(f.replace("_label", "_input")).read())
        key = "machine.CPU.temperature@phys.{gid}.{nodeid}.{coreid}".format(gid=gid, nid=nid, coreid=coreid)
        tags = 'gid:%d nid:%d labelfile:%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, f)
        value = inputtemp
        aggregatorcl.measure(key, tags, value, timestamp=now)

    #collect disks temperature thorugh smartctrl.

if __name__ == '__main__':
    print action()
