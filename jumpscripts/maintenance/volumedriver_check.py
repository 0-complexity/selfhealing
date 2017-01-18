from JumpScale import j
import psutil
import re
import json

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


def get_ovs_client():
    scl = j.clients.osis.getNamespace('system')
    ovs = scl.grid.get(j.application.whoAmI.gid).settings['ovs_credentials']
    return j.clients.openvstorage.get(ovs['ips'], (ovs['client_id'], ovs['client_secret']))


def find_move_targets(storagedrivers, vpool):
    # implement mechanism to find the best target to move the disks
    acc = j.clients.agentcontroller.get()

    results = acc.executeJumpscript(
        'greenitglobe',
        'volumedriver_memory_get',
        role='storagedriver',
        all=True,
        gid=j.application.whoAmI.gid,
        args={'vpool': vpool}
    )

    results = filter(lambda r: r['state'] == 'OK', results)
    results = sorted(results, key=lambda r: r['result'])

    osis = j.clients.osis.getNamespace('system')
    for result in results:
        node = osis.node.get('{}_{}'.format(result['gid'], result['nid']))
        for sd in storagedrivers:
            if sd['storage_ip'] in node.ipaddr:
                return sd['storagerouter_guid']

    return None


def clean_storagedriver(ps, vpool):
    # TODO:
    # 1- Find all volumes to move (from arakoon)
    # 2- Move volumes (if possible)
    # 3- Kill volumedriver
    ips = j.system.net.getIpAddresses()
    ovscl = get_ovs_client()
    sds = ovscl.get('/storagedrivers', params={'contents': 'storagerouter,vpool,vdisks_guids'})

    storagedriver = None
    for sd in sds['data']:
        if sd['storage_ip'] in ips and sd['mountpoint'] != '/mnt/{}'.format(vpool):
            storagedriver = sd
            break

    if storagedriver is None:
        # didnot find a storagedriver that is on this vpool+ip
        return

    # find the move target
    # make sure the current sotrage driver is out of the options
    sds['data'].remove(storagedriver)
    target = find_move_targets(sds['data'], vpool)

    if target is not None:
        # we can try moving vdisks before we kill it
        jobs = []
        for disk in storagedriver['vdisks_guids']:
            job = ovscl.post(
                '/vdisks/{}/move'.format(disk),
                data=json.dumps({'target_storagerouter_guid': target})
            )
            jobs.append(job)

    # kill the process
    ps.kill()


def get_memory_avg(agg, pool):
    key = 'process.memory.vmrss@phys.%d.%d.%s_%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, VOLUMEDRIVER_NAME, pool)
    stat = agg.statGet(key)

    if stat is None:
        return None

    return stat.m_avg


def get_vpool(ps):
    cmd = ' '.join(ps.cmdline())
    m = re.search(r'--mountpoint /mnt/(\w+)', cmd)
    if m is None:
        raise RuntimeError('cannot find the pool mount point for volumedriver pid: %s', ps.pid)

    return m.group(1)


def action():
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    # - Find all volumedriver processe
    for process in psutil.process_iter():
        if process.name() != VOLUMEDRIVER_NAME:
            continue

        vpool = get_vpool(process)
        mem = get_memory_avg(aggregatorcl, vpool)

        # check number of threads or memory
        if check_over_threads(len(process.threads())) or \
                check_over_memory(mem):
            # volumedriver must be cleaned up
            clean_storagedriver(process, vpool)


if __name__ == '__main__':
    action()
