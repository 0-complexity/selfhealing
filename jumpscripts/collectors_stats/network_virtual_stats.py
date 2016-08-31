from JumpScale import j
import time

descr = """
gather network statistics for virtual machines
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
category = "info.gather.nic"
period = 60  # always in sec
timeout = period * 0.2
enable = True
async = True
queue = 'process'
roles = []
log = False


def action():
    import libvirt

    connection = libvirt.open()
    scl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "stack")
    vmcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "vmachine")
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    # search stackid of the node where we execute this script
    stack = scl.search({'referenceId': str(j.application.whoAmI.nid)})[1]
    # list all vms running in this node
    domains = connection.listAllDomains()

    all_results = {}
    for domain in domains:

        vm = next(iter(vmcl.search({'referenceId': domain.UUIDString()})[1:]), None)
        if vm is None:
            continue

        for nic in vm['nics']:
            mac = nic['macAddress']
            path = j.system.fs.joinPaths('/sys/class/net', nic['deviceName'], 'statistics')
            result = {}

            now = j.base.time.getTimeEpoch()
            bytes_sent = int(j.system.fs.fileGetContents(path + '/tx_bytes'))
            bytes_recv = int(j.system.fs.fileGetContents(path + '/rx_bytes'))
            packets_sent = int(j.system.fs.fileGetContents(path + '/tx_packets'))
            packets_recv = int(j.system.fs.fileGetContents(path + '/rx_packets'))

            result['network.throughput.outgoing.virt.%s' % mac] = int(round(bytes_sent / 1024.0 * 1024, 0))
            result['network.throughput.incoming.virt.%s' % mac] = int(round(bytes_recv / 1024.0 * 1024, 0))
            result['network.packets.tx.virt.%s' % mac] = packets_sent
            result['network.packets.rx.virt.%s' % mac] = packets_recv

            all_results["%s_%s" % (vm['id'], mac)] = result

            # send data to aggregator
            for key, value in result.iteritems():
                tags = 'gid:%d nid:%d nic:%s mac:%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, nic['deviceName'], mac)
                aggregatorcl.measureDiff(key, tags, value, timestamp=now)

    return all_results

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    results = action()
    import yaml
    print yaml.dump(results)
