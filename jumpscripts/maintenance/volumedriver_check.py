from JumpScale import j
import psutil
import re

descr = """
This script make sure any rouge volumedriver is killed by checking its threads count and memory consumption
"""

organization = "jumpscale"
author = "muhamada@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['storagedriver']

# params
THREAD_THRESHOLD = 2000  # threads
MEMORY_THRESHOLD = 0.8

# do not change
VOLUMEDRIVER_NAME = 'volumedriver_fs'


def check_over_memory(value):
    # memory can be None if stats collection didn't report any values yet.
    # we handle this case here for simplicity.
    if value is None:
        return False

    # formula to find if this memory value is exceeding the threshold
    vm = psutil.virtual_memory()
    if float(value) / vm.total >= MEMORY_THRESHOLD:
        return True
    return False


def check_over_threads(count):
    return count >= THREAD_THRESHOLD


def clean_volumedriver(ps):
    # TODO:
    # 1- Find all volumes to move (from arakoon)
    # 2- Move volumes (if possible)
    # 3- Kill volumedriver
    pass


def get_memory_avg(agg, ps):
    cmd = ' '.join(ps.cmdline())
    m = re.search(r'--mountpoint /mnt/(\w+)', cmd)
    if m is None:
        raise RuntimeError('cannot find the pool mount point for volumedriver pid: %s', ps.pid)

    pool = m.group(1)
    key = 'process.memory.vmrss@phys.%d.%d.%s_%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, VOLUMEDRIVER_NAME, pool)
    stat = agg.statGet(key)

    if stat is None:
        return None

    return stat.m_avg


def action():
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    # - Find all volumedriver processe
    for process in psutil.process_iter():
        if process.name() != VOLUMEDRIVER_NAME:
            continue

        mem = get_memory_avg(aggregatorcl, process)

        # check number of threads or memory
        if check_over_threads(len(process.threads())) or \
                check_over_memory(mem):
            # volumedriver must be cleaned up
            clean_volumedriver(process)


if __name__ == '__main__':
    action()
