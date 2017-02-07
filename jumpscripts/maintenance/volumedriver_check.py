from JumpScale import j

descr = """
This script make sure any rouge volumedriver is killed by checking its threads count and memory consumption
"""

organization = "jumpscale"
author = "muhamada@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
period = 300  # always in sec
timeout = 3600  # an hour
startatboot = True
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['storagedriver']

# params
THREAD_THRESHOLD = 2000  # threads
MEMORY_THRESHOLD = 0.4

# do not change
VOLUMEDRIVER_NAME = 'volumedriver_fs'


class Reasons(object):
    def __init__(self):
        self._reasons = {}

    def reason(self, label, value):
        self._reasons[label] = str(value)

    @property
    def tags(self):
        return j.core.tags.getTagString(tags=self._reasons)


def check_over_memory(value, reasons):
    import psutil

    # memory can be None if stats collection didn't report any values yet.
    # we handle this case here for simplicity.
    if value is None:
        return False

    # formula to find if this memory value is exceeding the threshold
    vm = psutil.virtual_memory()
    percent = float(value) / vm.total
    if percent >= MEMORY_THRESHOLD:
        reasons.reason('memory.over', percent)
        return True
    return False


def check_over_threads(count, reasons):
    if count >= THREAD_THRESHOLD:
        reasons.reason('threads.over', count)
        return True

    return False


def check_volume_read(ovscl, driver, reasons):
    """
    Gets the list of all volumes available on this storagedriver and then
    try to read disk info of few random disks (10% of all disks)
    """
    import random
    import time

    print('checking driver {mountpoint}'.format(**driver))
    driver_obj = ovscl.get('/storagedrivers/{}'.format(driver['guid']), {'contents': 'cluster_node_config,vdisks_guids'})
    vdisks = driver_obj['vdisks_guids']
    if len(vdisks) == 0:
        return False

    if driver_obj['cluster_node_config']['network_server_uri'].startswith('tcp://'):
        protocol = 'openvstorage+tcp'
    else:
        protocol = 'openvstorage+rdma'
    base_url = protocol + ':{storage_ip}:{ports[edge]}'.format(**driver)

    osis = j.clients.osis.getNamespace('cloudbroker')
    random.shuffle(vdisks)
    scores = list()
    check_count = max(1, int(len(vdisks) * 10 / 100))
    disks = []

    for guid in vdisks:
        try:
            vdisk = ovscl.get('/vdisks/{}'.format(guid))
        except:
            print('error getting vdiks %s' % guid)
            continue

        if vdisk['is_vtemplate']:
            continue

        print('checking if disk %s is actually in use by ovc' % guid)
        count = osis.disk.search({
            'referenceId': {'$regex': '{}$'.format(guid)},
            'status': {'$ne': 'DESTROYED'},
        })[0]

        if count == 0:
            # disk is not used by the system
            print('disk %s is not in use in ovc' % guid)
            continue

        disks.append(vdisk)
        if len(disks) == check_count:
            break

    for vdisk in disks:
        url = '{}{}'.format(base_url, vdisk['devicename'][:-4])

        try:
            print('qemu-img info {}'.format(url))
            code, out, err = j.do.execute('qemu-img info {}'.format(url), timeout=10, outputStdout=False, dieOnNonZeroExitCode=False)
        except RuntimeError:
            # Failed to read the info (probably timedout)
            print('timedout reading {}'.format(url))
            scores.append(vdisk['guid'])
            continue

        if code != 0:
            scores.append(vdisk['guid'])

    if len(scores) == 0:
        return False

    for x in range(10):
        time.sleep(5)

        driver_obj = ovscl.get('/storagedrivers/{}'.format(driver['guid']), {'contents': 'vdisks_guids'})
        vdisks = driver_obj['vdisks_guids']

        checks = list(scores)
        for vdisk in checks:
            if vdisk not in vdisks:
                scores.remove(vdisk)
                continue

            try:
                vdisk = ovscl.get('/vdisks/{}'.format(vdisk))
            except:
                continue

            url = '{}{}'.format(base_url, vdisk['devicename'][:-4])

            try:
                print('qemu-img info {}'.format(url))
                code, out, err = j.do.execute('qemu-img info {}'.format(url), timeout=10, outputStdout=False, dieOnNonZeroExitCode=False)
                if code == 0:
                    scores.remove(vdisk['guid'])
                else:
                    reasons.reason('vdisk.{}'.format(vdisk['guid']), 'read-error')
            except RuntimeError:
                # Failed to read the info (probably timedout)
                reasons.reason('vdisk.{}'.format(vdisk['guid']), 'timeout')
                print('timedout reading {}'.format(url))
                continue

        if len(scores) == 0:
            break

    if len(scores) == 0:
        return False

    reasons.reason('scores', len(scores))
    return True


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

    results = filter(lambda r: r['state'] == 'OK' and r['result'] < 50, results)

    osis = j.clients.osis.getNamespace('system')
    targets = set()
    for result in results:
        node = osis.node.get('{}_{}'.format(result['gid'], result['nid']))
        for sd in storagedrivers:
            if sd['storage_ip'] in node.ipaddr:
                targets.add(sd['storagerouter_guid'])
                break

    return targets


def wait_all_jobs(ovscl, jobs):
    import time

    max_wait_time = 120  # 2 minutes
    sleep_per_wait = 2  # seconds
    while max_wait_time > 0:
        st = time.time()
        for i in range(len(jobs) - 1, -1, -1):
            job = jobs[i]
            task_metadata = ovscl.get('/tasks/{0}/'.format(job))
            if task_metadata['status'] in ('FAILURE', 'SUCCESS'):
                jobs.pop(i)
        if len(jobs) == 0:
            break
        time.sleep(sleep_per_wait)
        max_wait_time -= (time.time() - st)


def clean_storagedriver(ps, vpool):
    import json
    from itertools import cycle

    ips = j.system.net.getIpAddresses()
    ovscl = get_ovs_client()
    sds = ovscl.get('/storagedrivers', params={'contents': 'storagerouter,vpool,vdisks_guids'})

    storagedriver = None
    for sd in sds['data']:
        if sd['storage_ip'] in ips and sd['mountpoint'] == '/mnt/{}'.format(vpool):
            storagedriver = sd
            break

    if storagedriver is None:
        # didnot find a storagedriver that is on this vpool+ip
        return

    # find the move target
    # make sure the current sotrage driver is out of the options
    sds['data'].remove(storagedriver)
    targets = find_move_targets(sds['data'], vpool)

    if targets:
        # we can try moving vdisks before we kill it
        jobs = []
        roundrobin = cycle(targets)
        for disk in storagedriver['vdisks_guids']:
            target = next(roundrobin)

            job = ovscl.post(
                '/vdisks/{}/move'.format(disk),
                data=json.dumps({'target_storagerouter_guid': target})
            )
            jobs.append(job)

        wait_all_jobs(ovscl, jobs)


def get_memory_avg(agg, pool):
    key = 'process.memory.vmrss@phys.%d.%d.%s_%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, VOLUMEDRIVER_NAME, pool)
    stat = agg.statGet(key)

    if stat is None:
        return None

    return stat.m_avg


def get_vpool(ps):
    import re

    cmd = ' '.join(ps.cmdline())
    m = re.search(r'--mountpoint /mnt/(\w+)', cmd)
    if m is None:
        raise RuntimeError('cannot find the pool mount point for volumedriver pid: %s', ps.pid)

    return m.group(1)


def get_storage_drivers(ovscl):
    ips = j.system.net.getIpAddresses()
    drivers = ovscl.get('/storagedrivers', params={'contents': 'storagedriver'})

    storage_drivers = []
    for sd in drivers['data']:
        if sd['storage_ip'] in ips:
            storage_drivers.append(sd)

    return storage_drivers


def filter_storage_driver(drivers, vpool):
    matches = filter(lambda sd: sd['mountpoint'] == '/mnt/{}'.format(vpool), drivers)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        return None
    else:
        raise RuntimeError('found more than one match')


def is_active(vpool):
    active = j.system.platform.ubuntu.statusService(
        'ovs-volumedriver_{}'.format(vpool)
    )

    if not active:
        return False

    # check mount point
    return j.system.fs.isMount('/mnt/{}'.format(vpool))


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    import psutil

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    ovscl = get_ovs_client()

    storage_drivers = get_storage_drivers(ovscl)

    # - Find all volumedriver processe
    for process in psutil.process_iter():
        if process.name() != VOLUMEDRIVER_NAME:
            continue

        vpool = get_vpool(process)
        if not is_active(vpool):
            print('volumedriver {} is not active'.format(vpool))
            continue

        print('volumedriver {} is active: running health checks ...'.format(vpool))
        storage_driver = filter_storage_driver(storage_drivers, vpool)
        mem = get_memory_avg(aggregatorcl, vpool)

        # check number of threads, memory, or if vdisks are not readable
        reasons = Reasons()
        if check_over_threads(len(process.threads()), reasons) or \
                check_over_memory(mem, reasons) or \
                check_volume_read(ovscl, storage_driver, reasons):

            # volumedriver must be cleaned up
            print("CLEANING UP", vpool)
            clean_storagedriver(process, vpool)
            eco_tags = j.core.tags.getObject()
            eco_tags.tagSet('nid', nid)
            eco_tags.labelSet('volumedriver.kill')
            j.errorconditionhandler.raiseOperationalWarning(
                message='kill rogue volumedriver %s on nid:%s and gid:%s ' % (vpool, nid, gid),
                category='selfhealing',
                tags=str(eco_tags) + ' %s' % reasons.tags
            )

            j.system.platform.ubuntu.restartService('ovs-volumedriver_{}'.format(vpool))


if __name__ == '__main__':
    action()
