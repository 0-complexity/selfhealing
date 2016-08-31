from JumpScale import j

descr = """
Checks status of all physical disks and partitions on all nodes by checking free disk space on mount points
(except if / of mount point contains .dontreportusage - which is needed as an exception for read and write cache for OVS)

Throws WARNING per mount point if >90% used, throws ERROR per mount point if >95% used

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
period = 600

log = True



def action():
    import JumpScale.lib.diskmanager
    result = dict()
    pattern = None

    if j.application.config.exists('gridmonitoring.disk.pattern'):
        pattern = j.application.config.getStr('gridmonitoring.disk.pattern')

    disks = j.system.platform.diskmanager.partitionsFind(
        mounted=True, prefix='', minsize=0, maxsize=None)

    def diskfilter(disk):
        return not (pattern and j.codetools.regex.match(pattern, disk.path))

    def disktoStr(disk):
        if disk.mountpoint:
            freesize, freeunits = j.tools.units.bytes.converToBestUnit(disk.free, 'M')
            size = j.tools.units.bytes.toSize(disk.size, 'M', freeunits)
            return "%s on %s %.02f/%.02f %siB free" % (disk.path, disk.mountpoint, freesize, size, freeunits)
        else:
            return '%s %s' % (disk.path, disk.model)

    def getLogsDisks(disks):
        """Return a list of disks that might have logs written to it"""
        disks = sorted(disks, key=lambda d: d.mountpoint)
        disks = filter(disks, lambda d: d.mountpoint in ['/', '/opt', '/var'])
        if len(disks) > 1:
            disks = disks[1:]
        return disks

    logsdisks = getLogsDisks(disks)

    results = list()
    for disk in filter(diskfilter, disks):
        result = {'category': 'Disks'}
        result['path'] = disk.path
        checkusage = not (disk.mountpoint and j.system.fs.exists(j.system.fs.joinPaths(disk.mountpoint, '.dontreportusage')))
        result['state'] = 'OK'
        result['message'] = disktoStr(disk)
        if disk.free and disk.size:
            freepercent = (disk.free / float(disk.size)) * 100
            if checkusage and disk in logsdisks and (freepercent < 20):
                jumpscript = j.clients.redisworker.getJumpscriptFromName('0-complexity', 'logs_truncate')
                j.clients.redisworker.execJumpscript(jumpscript=jumpscript, mountpoint=disk.mountpoint)
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
    print action()
