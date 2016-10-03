from JumpScale import j

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
    import libvirt

    connection = LibvirtUtil()
    dcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "disk")
    vmcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "vmachine")
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    # list all vms running in this node
    domains = connection.connection.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_RUNNING)

    all_results = {}
    for domain in domains:
        vm = next(iter(vmcl.search({'referenceId': domain.UUIDString()})[1:]), None)
        if vm is None:
            continue

        domaindisks = list(connection.get_domain_disks(domain))

        # get all the disks attached to a vm
        disks = dcl.search({'id': {'$in': vm['disks']}})[1:]

        # get statistics for each disks
        for disk in disks:
            dev = connection.get_domain_disk(disk['referenceId'], domaindisks)
            if not dev:
                continue

            stats = domain.blockStats(dev)
            now = j.base.time.getTimeEpoch()
            read_count, read_bytes, write_count, write_bytes, _ = stats

            result = {}
            result['disk.iops.read'] = read_count
            result['disk.iops.write'] = write_count
            result['disk.throughput.read'] = int(round(read_bytes / 1024, 0))  # IN KB
            result['disk.throughput.write'] = int(round(write_bytes / 1024, 0))  # IN KB

            all_results["%s_%s" % (vm['id'], dev)] = result

            # send data to aggregator
            for key, value in result.iteritems():
                key = "%s@virt.%s" % (key, disk['id'])
                tags = 'gid:%d nid:%d device:%s vdiskid:%s type:virtual' % (j.application.whoAmI.gid, j.application.whoAmI.nid, dev, disk['id'])
                aggregatorcl.measureDiff(key, tags, value, timestamp=now)

    return {'results': all_results, 'errors': []}

if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    rt = action()
    import yaml
    print(yaml.safe_dump(rt['results'], default_flow_style=False))
