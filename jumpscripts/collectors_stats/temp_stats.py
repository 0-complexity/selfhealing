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
log = False


def action():
    from multiprocessing import Process
    import glob
    import re
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
            value = inputtemp / 1000  # inputtemp is in millidegree Celsius
            now = j.base.time.getTimeEpoch()
            aggregatorcl.measure(key, tags, value, timestamp=now)

    #  collect disks temperature thorugh smartctrl.
    j.system.platform.ubuntu.checkInstall('smartmontools', 'smartctl')

    def disktemp(disk):
        cmd = 'smartctl -A /dev/{disk}'.format(disk=disk)
        pat = "^(190|194).*?(?P<temp>\d+)(?:\(.*\))?$"
        rc, out = j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
        if rc == 0 and out:
            for match in re.finditer(pat, out, re.M):
                current = int(match.group('temp'))
                print("Disk {} at {}".format(disk, current))
                key = "machine.disk.temperature@phys.{gid}.{nid}.{disk}".format(gid=gid, nid=nid, disk=disk)
                tags = 'gid:%d nid:%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)
                now = j.base.time.getTimeEpoch()
                aggregatorcl.measure(key, tags, current, timestamp=now)
                break

    # disks are ssd, hdd, nvm
    disks = glob.glob("/sys/block/sd*") + glob.glob("/sys/block/hd*") + glob.glob("/sys/block/nvm*")

    processes = []
    for disk in disks:
        disk = j.system.fs.getBaseName(disk)
        p = Process(target=disktemp, args=(disk,))
        p.start()
        processes.append(p)
    map(lambda p: p.join(), processes)

if __name__ == '__main__':
    action()
