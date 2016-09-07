from JumpScale import j
import time

descr = """
gather statistics about virtual disks
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
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

roles = ['cpunode']

def action():
    from CloudscalerLibcloud.utils.libvirtutil import LibvirtUtil
    import urlparse

    connection = LibvirtUtil()
    dcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "disk")
    scl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "stack")
    vmcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "vmachine")
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    # search stackid of the node where we execute this script
    stack = scl.search({'referenceId': str(j.application.whoAmI.nid)})[1]
    # list all vms running in this node
    domains = connection.list_domains()

    all_results = {}
    for domain in domains:
        vm = next(iter(vmcl.search({'referenceId': domain['id']})[1:]), None)
        if vm is None:
            continue

        domain = connection.get_domain(domain['id'])
        domaindisks = list(connection.get_domain_disks(domain['XMLDesc']))

        # TODO move get_domain_disk into LibvirtUtil
        def get_domain_disk(name):
            name = name.strip('/')
            for disk in domaindisks:
                source = disk.find('source')
                if source is not None:
                    if source.attrib['name'].strip('/') == name:
                        target = disk.find('target')
                        return target.attrib['dev']

        # get all the disks attached to a vm
        disks = dcl.search({'id': {'$in': vm['disks']}})[1:]

        # get statistics for each disks
        for disk in disks:
            parsed_url = urlparse.urlparse(disk['referenceId'])
            dev = get_domain_disk(parsed_url.path)

            libvirt_domain = connection._get_domain(domain['id'])
            stats = libvirt_domain.blockStats(dev)
            now = j.base.time.getTimeEpoch()
            read_count, read_bytes, write_count, write_bytes, _ = stats

            result = {}
            result['disk.iops.read'] = read_count
            result['disk.iops.write'] = write_count
            result['disk.throughput.read'] = int(round(read_bytes / 1024 * 1024, 0))
            result['disk.throughput.write'] = int(round(write_bytes / 1024 * 1024, 0))

            all_results["%s_%s" % (vm['id'], dev)] = result

            # send data to aggregator
            for key, value in result.iteritems():
                key = "%s@virt.%s" % (key, disk['id'])
                tags = 'gid:%d nid:%d device:%s vdiskid:%s type:virtual' % (j.application.whoAmI.gid, j.application.whoAmI.nid, dev, disk['id'])
                aggregatorcl.measureDiff(key, tags, value, timestamp=now)

    return {'results': all_results, 'errors': []}

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    rt = action()
    import yaml
    print yaml.dump(rt['results'])
