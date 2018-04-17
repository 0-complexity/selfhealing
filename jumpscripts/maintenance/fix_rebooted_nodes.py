from JumpScale import j
import time

descr = """
This script ensures all vms and router oses reboot after a node reboot.
"""

organization = "jumpscale"
author = "tareka@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
period = 180  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
queue = 'process'
roles = ['cpunode']


def action():

    out = j.system.fs.fileGetContents('/proc/uptime')
    up_time = out.strip('\n').split(' ')
    if float(up_time[0]) > 300:
        return

    #get model data ( virtual machines and router oses)
    import libvirt
    nid = j.application.whoAmI.nid
    scl = j.clients.osis.getNamespace('system')
    ccl = j.clients.osis.getNamespace('cloudbroker')
    vcl = j.clients.osis.getNamespace('vfw')
    pcl = j.clients.portal.getByInstance('main')
    result = ccl.stack.searchOne({'referenceId': str(nid)})
    if result:
        stack_id = result['id']
    else:
        raise RuntimeError('This node id does not belong to a cpu node please check where you are running this script')
    # get all running virtual machines on this node
    model_virtual_machines = ccl.vmachine.search({'status': 'RUNNING', 'stackId': stack_id})[1:]
    time_limit = j.base.time.getTimeEpoch() - 300
    for machine in ccl.vmachine.search({'status': 'HALTED',  'stackId': stack_id})[1:]:
        results = scl.audit.search({"tags": {"$regex":'.*machineId:%s.*' % machine['id']},
                                    "user": "Operation System Action",
                                    "call": "/restmachine/cloudapi/machines/stop",
                                    "timestamp": {"$gt": time_limit} })
        if results:
            model_virtual_machines.append(machine)

    # get all running vfws (routeroses) on this node
    all_virtual_firewalls = vcl.virtualfirewall.search({'nid': nid, 'type': 'routeros'})[1:]

    # get running domain from libvirt on this node
    libvirt_conn = libvirt.open()
    network_ids = []
    domains = [domain.state() for domain in libvirt_conn.listAllDomains() if domain.state()[0] == libvirt.VIR_DOMAIN_RUNNING]
    domains_uuid = [domain.UUIDString() for domain in domains]
    for domain in domains:
        if domain.name().startswith('routeros_'):
            network_ids.append(int(domain.name().replace('routeros_', ''), 16))
    # check for halted vms and respawn
    for machine_model in model_virtual_machines:
        if machine_model['referenceId'] in domains_uuid:
            continue
        pcl.actors.cloudbroker.machine.start(machineId=machine_model['id'], reason='node reboot')
    # check for halted router oses and respawn
    for vfw in all_virtual_firewalls:
        cloudspace = ccl.cloudspace.searchOne({'networkId': vfw['id']})
        if not cloudspace:
            j.errorcondtiion.raiseOperationWarning('no cloudspace with networkId %s available' % vfw['networkid'])
        if cloudspace['status'] != 'DEPLOYED' or vfw['id'] in network_ids:
            continue
        pcl.actors.cloudbroker.cloudspace.startVFW(cloudspaceId=cloudspace['id'])

if __name__ == '__main__':
    action()
