from JumpScale import j

descr = """
healthcheck that monitors rouge volumedriver  by checking its threads count and memory consumptio
"""

organization = "jumpscale"
author = "muhamada@greenitglobe.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 300  # always in sec
timeout = 3600  # an hour
startatboot = True
order = 1
enable = True
async = True
log = True
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
        self.messages = []

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
        reasons.messages.append("{}/{} memory".format(percent * 100, MEMORY_THRESHOLD * 100))
        return True
    return False


def check_over_threads(count, reasons):
    if count >= THREAD_THRESHOLD:
        reasons.reason('threads.over', count)
        reasons.messages.append("{}/{} threads".format(count, THREAD_THRESHOLD))
        return True

    return False


def check_volume_read(ovscl, driver, reasons):
    """
    Gets the list of all volumes available on this storagedriver and then
    try to read disk info of few random disks (10% of all disks)
    """
    import random
    from urlparse import urlparse

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
        dbdisks = osis.disk.search({
            'referenceId': {'$regex': '{}$'.format(guid)},
            'status': {'$ne': 'DESTROYED'},
        })[1:]

        if not dbdisks:
            # disk is not used by the system
            print('disk %s is not in use in ovc' % guid)
            continue

        parsedurl = urlparse(dbdisks[0]['referenceId'])
        path = parsedurl.path.split('@', 1)[0]
        vdisk['devicepath'] = path

        disks.append(vdisk)
        if len(disks) == check_count:
            break

    for vdisk in disks:
        url = '{}{}'.format(base_url, vdisk['devicepath'])

        try:
            print('qemu-img info {}'.format(url))
            code, out, err = j.do.execute(['qemu-img', 'info', url], timeout=10, outputStdout=False, dieOnNonZeroExitCode=False, useShell=False)
            if code != 0:
                reasons.messages.append("Failed to read volume {} ({})".format(vdisk['devicename'], vdisk['guid']))
                reasons.reason('vdisk.{}'.format(vdisk['guid']), 'read-error')
        except RuntimeError:
            # Failed to read the info (probably timedout)
            reasons.reason('vdisk.{}'.format(vdisk['guid']), 'timeout')
            reasons.messages.append("Reading of volume timedout {} ({})".format(vdisk['devicename'], vdisk['guid']))
            print('timedout reading {}'.format(url))


def get_ovs_client():
    scl = j.clients.osis.getNamespace('system')
    ovs = scl.grid.get(j.application.whoAmI.gid).settings['ovs_credentials']
    return j.clients.openvstorage.get(ovs['ips'], (ovs['client_id'], ovs['client_secret']))


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
    import psutil
    results = []

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    ovscl = get_ovs_client()

    storage_drivers = get_storage_drivers(ovscl)

    # - Find all volumedriver processe
    for process in psutil.process_iter():
        try:
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
            check_over_threads(len(process.threads()), reasons)
            check_over_memory(mem, reasons)
            check_volume_read(ovscl, storage_driver, reasons)
            if reasons.messages:
                message = "\n".join(["Volumedriver {} has some problems:".format(vpool)] + reasons.messages)
                msg = {'category': 'Volumedriver',
                       'state': 'WARNING',
                       'message': message}
                results.append(msg)
            else:
                message = "Volumedriver {} has no problems.".format(vpool)
                msg = {'category': 'Volumedriver',
                       'state': 'OK',
                       'message': message}
                results.append(msg)
        except psutil.NoSuchProcess:
            pass  # process has stopped no need to monitor it
    return results


if __name__ == '__main__':
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
