from JumpScale import j
import time

descr = """
Gathers following statistics about the physical disks:
- time_read
- time_write
- count_read
- count_write
- kbytes_read
- kbytes_write
- MB_read
- MB_write
- space_free_mb
- space_used_mb
- space_percent
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "disk.monitoring"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
queue = 'process'
log = False

roles = []


def action():
    import psutil

    dcl = j.clients.osis.getCategory(j.core.osis.client, "system", "disk")
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    partitions = psutil.disk_partitions()
    # disk counters
    counters = psutil.disk_io_counters(True)
    now = j.base.time.getTimeEpoch()
    all_results = {}

    def get_partition(path):
        for partition in partitions:
            if path in partition.device:
                return partition

    for path, counter in counters.iteritems():
        if path.startswith('ram'):
            continue  # skip ram devices
        results = {'time_read': 0, 'time_write': 0, 'count_read': 0, 'count_write': 0,
                   'kbytes_read': 0, 'kbytes_write': 0,
                   'MB_read': 0, 'MB_write': 0,
                   'space_free_mb': 0, 'space_used_mb': 0, 'space_percent': 0}

        odisk = dcl.new()
        oldkey = rediscl.hget('disks', path)
        odisk.nid = j.application.whoAmI.nid
        odisk.gid = j.application.whoAmI.gid

        counter = counters[path]
        read_count, write_count, read_bytes, write_bytes, read_time, write_time = counter
        results['time_read'] = read_time
        results['time_write'] = write_time
        results['count_read'] = read_count
        results['count_write'] = write_count

        results['kbytes_read'] = int(round(read_bytes / 1024, 0))
        results['kbytes_write'] = int(round(write_bytes / 1024, 0))
        results['MB_read'] = int(round(read_bytes / (1024 * 1024), 0))
        results['MB_write'] = int(round(write_bytes / (1024 * 1024), 0))
        partition = get_partition(path)
        if partition is not None:
            usage = psutil.disk_usage(partition.mountpoint)
            results['space_free_mb'] = int(round(usage.free / (1024 ** 2)))
            results['space_used_mb'] = int(round(usage.used / (1024 ** 2)))
            results['space_percent'] = int(round((float(usage.used) / float(usage.total)), 2))
            odisk.free = results['space_free_mb']
            odisk.size = int(usage.total / 1024 ** 2)
            odisk.path = partition.device
            odisk.mountpoint = partition.mountpoint
            odisk.fs = partition.fstype
            odisk.mounted = True
        else:
            odisk.path = j.system.fs.joinPaths('/dev', path)
            odisk.mounted = False



        ckey = odisk.getContentKey()
        if ckey != oldkey:
            print("Disk %s changed" % (path))
            dcl.set(odisk)
            rediscl.hset('disks', path, ckey)

        # send stats to redis aggregator
        stats = {
            'disk.iops.read': {
                'value_key': 'count_read',
                'type': 'D'
            },
            'disk.iops.write': {
                'value_key': 'count_write',
                'type': 'D'
            },
            'disk.throughput.read': {
                'value_key': 'kbytes_read',
                'type': 'D'
            },
            'disk.throughput.write': {
                'value_key': 'kbytes_write',
                'type': 'D'
            }
        }
        for key, info in stats.iteritems():
            key = '%s@phys.%d.%d.%s' % (key, j.application.whoAmI.gid, j.application.whoAmI.nid, path)
            tags = 'gid:%d nid:%d device:%s type:physical' % (j.application.whoAmI.gid, j.application.whoAmI.nid, path)
            value = results[info['value_key']]
            aggregatorcl._measure(key, tags, value, type=info['type'], timestamp=now)

        all_results[path] = results

    return {'results': all_results, 'errors': []}

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    rt = action()
    import yaml
    print(yaml.safe_dump(rt['results'], default_flow_style=False))
