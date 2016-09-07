from JumpScale import j
from constant import PERIOD

descr = """
Checks the temperature on the system.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitoring.processes"
roles = ['node']
period = PERIOD  # 1min
enable = True
async = True
queue = 'process'
log = True


def action():
    from multiprocessing import Process
    import glob
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))
    gid, nid = j.application.whoAmI.gid, j.application.whoAmI.nid
    labeled = sorted(glob.glob("/sys/class/hwmon/*/temp*_label"))

    for f in labeled:
        label = open(f).read()  # Core 0
        if "core" in label.lower():
            coreid = int(label.split()[1])
            inputtemp = int(open(f.replace("_label", "_input")).read())
            key = "machine.CPU.temperature@phys.{gid}.{nid}.{coreid}".format(gid=gid, nid=nid, coreid=coreid)
            tags = 'gid:%d nid:%d labelfile:%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, f)
            value = inputtemp
            now = j.base.time.getTimeEpoch()
            aggregatorcl.measure(key, tags, value, timestamp=now)

    #  collect disks temperature thorugh smartctrl.
    def disktemp(disk):
        cmd = 'smartctl -A /dev/{disk}'.format(disk=disk)
        pat = "(\d+) \(Min/Max (\d+)/(\d+)\)"
        rc, out = j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
        if rc == 0 and out:
            current, mint, maxt = map(int, re.findall(pat, out)[0])
            key = "machine.disk.temperature@phys.{gid}.{nid}.{disk}".format(gid=gid, nid=nid, disk=disk)
            tags = 'gid:%d nid:%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)
            value = current
            now = j.base.time.getTimeEpoch()
            aggregatorcl.measure(key, tags, value, timestamp=now)

    # disks are ssd, hdd, nvm
    disks = glob.glob("/sys/block/sd*").extend(glob.glob("/sys/block/hd*")).extend(glob.glob("/sys/block/nvm*"))
    for disk in disks:
        p = Process(target=disktemp, args=(disk))
        p.start()
        p.join()

if __name__ == '__main__':
    print action()
