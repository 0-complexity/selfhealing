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
    from collections import namedtuple
    treshold = namedtuple('treshold', 'warning truncate error')
    # tresholds for disk usage warning, truncate logs, error
    # if truncagte logs is negative dont execute truncate logs
    TRESHOLDS = {
        'ALBA-CACHE': treshold(8, -1, 5),
        'ALBA-STORAGE': treshold(10, -1, 5),
        'DEFAULT': treshold(20, 15, 10),
    }
    import psutil
    import os
    result = dict()
    pattern = None
    cpunode = 'cpunode' in j.core.grid.roles

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
        # Check if it is a cache partition
        is_cache = False
        for dir_name in os.listdir(partition.mountpoint):
            name_list = dir_name.split('_')
            if len(name_list) > 2 and name_list[1] == 'write':
                is_cache = True
                break

        checkusage = not (partition.mountpoint and
                          j.system.fs.exists(j.system.fs.joinPaths(partition.mountpoint, '.dontreportusage')) or is_cache)
        result['state'] = 'OK'
        usage = None
        if partition.mountpoint:
            usage = psutil.disk_usage(partition.mountpoint)
        result['message'] = disktoStr(partition, usage)
        if usage is not None:
            if 'alba-asd' in partition.mountpoint:
                if cpunode:
                    tresholds = TRESHOLDS['ALBA-CACHE']
                else:
                    tresholds = TRESHOLDS['ALBA-STORAGE']
            else:
                tresholds = TRESHOLDS['DEFAULT']
            freepercent = (usage.free / float(usage.total)) * 100
            if checkusage and tresholds.truncate > 0 and (freepercent < tresholds.truncate):
                jumpscript = j.clients.redisworker.getJumpscriptFromName('0-complexity', 'logs_truncate')
                j.clients.redisworker.execJumpscript(jumpscript=jumpscript, freespace_needed=40.0)
            if checkusage and (freepercent < tresholds.warning):
                result['state'] = 'WARNING'
                result['uid'] = partition.device
            if checkusage and (freepercent < tresholds.error):
                result['state'] = 'ERROR'
                result['uid'] = partition.device
        results.append(result)

    if not results:
        results.append({'message': 'No disks available', 'state': 'OK', 'category': 'Disks'})

    return results


if __name__ == "__main__":
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
