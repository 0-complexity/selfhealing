from JumpScale import j

descr = """
Checks status of all physical disks and partitions on all nodes, reporting back the free disk space on mount points.

(except if / of mount point contains .dontreportusage - which is needed as an exception for read and write cache for OVS)

Throws WARNING per mount point if >90% used, throws ERROR per mount point if >95% used.
"""

organization = "jumpscale"
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = True
queue = 'process'
roles = []
enable = True
period = 60
roles = ['node']
log = True


def action():
    import psutil
    result = dict()
    pattern = None

    if j.application.config.exists('gridmonitoring.disk.pattern'):
        pattern = j.application.config.getStr('gridmonitoring.disk.pattern')

    def diskfilter(partition):
        return not (pattern and j.codetools.regex.match(pattern, partition.device))

    def disktoStr(partition, usage):
        freesize, freeunits = j.tools.units.bytes.converToBestUnit(usage.free)
        size = j.tools.units.bytes.toSize(usage.total, '', freeunits)
        return "%s on %s %.02f/%.02f %siB free" % (partition.device, partition.mountpoint, freesize, size, freeunits)

    results = list()
    checked_devices = []
    for partition in filter(diskfilter, psutil.disk_partitions()):
        if partition.device in checked_devices:
            continue

        checked_devices.append(partition.device)

        result = {'category': 'Disks'}
        result['path'] = j.system.fs.getBaseName(partition.device)
        checkusage = not (partition.mountpoint and
                          j.system.fs.exists(j.system.fs.joinPaths(partition.mountpoint, '.dontreportusage')))
        result['state'] = 'OK'
        usage = None
        if partition.mountpoint:
            usage = psutil.disk_usage(partition.mountpoint)
        result['message'] = disktoStr(partition, usage)
        if usage is not None:
            freepercent = (usage.free / float(usage.total)) * 100
            if checkusage and (freepercent < 20):
                jumpscript = j.clients.redisworker.getJumpscriptFromName('0-complexity', 'logs_truncate')
                j.clients.redisworker.execJumpscript(jumpscript=jumpscript, freespace_needed=40.0)
            if checkusage and (freepercent < 10):
                j.errorconditionhandler.raiseOperationalWarning(result['message'], 'monitoring')
                result['state'] = 'WARNING'
                result['uid'] = result['message']
            if checkusage and (freepercent < 5):
                j.errorconditionhandler.raiseOperationalCritical(result['message'], 'monitoring', die=False)
                result['state'] = 'ERROR'
                result['uid'] = result['message']
        results.append(result)

    if not results:
        results.append({'message': 'No disks available', 'state': 'OK', 'category': 'Disks'})

    return results


if __name__ == "__main__":
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
