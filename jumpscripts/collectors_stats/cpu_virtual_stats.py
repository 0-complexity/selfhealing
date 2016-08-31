from JumpScale import j
import re


descr = """
gather statistics about cpu utilisation of virtual machines
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitoring.processes"
period = 60  # always in sec
timeout = period * 0.2
enable = True
async = True
queue = 'process'
log = False

roles = []


def action():
    import libvirt

    connection = libvirt.open()
    scl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "stack")
    vmcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "vmachine")
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    # search stackid of the node where we execute this script
    stack = scl.simpleSearch({'referenceId': str(j.application.whoAmI.nid)})[0]
    # list all vms running in this node
    vms = vmcl.simpleSearch({'stackId': stack['id'], 'status': 'RUNNING'})

    all_results = {}
    for vm in vms:
        result = {}
        domain = connection.lookupByUUIDString(vm['referenceId'])
        state, maxMem, memory, nrVirtCpu, cpuTime, = domain.info()
        now = j.base.time.getTimeEpoch()

        key = 'machine.CPU.utilisation.virt.%d' % vm['id']
        value = int(cpuTime)
        tags = 'gid:%d nid:%d vmid:' % (j.application.whoAmI.gid, j.application.whoAmI.nid, vm['id'])
        aggregatorcl.measure(key, tags, value, timestamp=now)

        all_results[vm['id']] = value

    return all_results

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    rt = action()
    import yaml
    print yaml.dump(rt['results'])
