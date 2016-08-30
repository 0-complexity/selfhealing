from JumpScale import j
import time

descr = """
gather statistics about disks
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "disk.monitoring"
period = 300 #always in sec
timeout = period * 0.2
order = 1
enable=True
async=True
queue='process'
log=False

roles = []

def action():
    import JumpScale.lib.diskmanager
    import statsd
    import psutil

    dcl = j.clients.osis.getCategory(j.core.osis.client, "system", "disk")
    rediscl = j.clients.redis.getByInstance('system')
    stats = statsd.StatsClient()
    pipe = stats.pipeline()

    disks = j.system.platform.diskmanager.partitionsFind(mounted=True, prefix='', minsize=0, maxsize=None)

    #disk counters
    counters=psutil.disk_io_counters(True)

    for disk in disks:

        results = {'time_read': 0, 'time_write': 0, 'count_read': 0, 'count_write': 0,
                   'kbytes_read': 0, 'kbytes_write': 0, 
                   'space_free_mb': 0, 'space_used_mb': 0, 'space_percent': 0}
        path=disk.path.replace("/dev/","")

        odisk = dcl.new()
        oldkey = rediscl.hget('disks', path)
        odisk.nid = j.application.whoAmI.nid
        odisk.gid = j.application.whoAmI.gid

        if counters.has_key(path):
            counter=counters[path]
            read_count, write_count, read_bytes, write_bytes, read_time, write_time=counter
            results['time_read'] = read_time
            results['time_write'] = write_time
            results['count_read'] = read_count
            results['count_write'] = write_count

            read_bytes=int(round(read_bytes/1024,0))
            write_bytes=int(round(write_bytes/1024,0))
            results['kbytes_read'] = read_bytes
            results['kbytes_write'] = write_bytes
            results['space_free_mb'] = int(round(disk.free))
            results['space_used_mb'] = int(round(disk.size-disk.free))
            results['space_percent'] = int(round((float(disk.size-disk.free)/float(disk.size)),2))

        for key,value in disk.__dict__.iteritems():
            odisk.__dict__[key]=value

        ckey = odisk.getContentKey()
        if ckey != oldkey:
            print("Disk %s changed" % (path))
            dcl.set(odisk)
            rediscl.hset('disks', path, ckey)

        for key, value in results.iteritems():
            pipe.gauge("%s_%s_disk_%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid, path, key), value)

    result = pipe.send()
    return {'results': result, 'errors': []}

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('processmanager')
    action()
