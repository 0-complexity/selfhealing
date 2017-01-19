from JumpScale import j

descr = """
Check the bandwith consumption of the network utilized by the virtual machine
> 8k packets WARNING
> 10k packets  ERROR
"""
organization = "cloudscalers"
author = "deboeckj@greenitglobe.com"
order = 1
enable = True
async = True
log = True
queue = 'process'
period = 180
roles = ['cpunode']
category = "monitor.healthcheck"


def tag_vm(ccl, vm, state, con):
    tagobject = j.core.tags.getObject()
    change = False
    if state == 'OK':
        change = tagobject.tags.pop('packetlimit', None) is not None
    elif state in ['ERROR', 'WARNING']:
        change = True
        packetlimit = tagobject.tags.get('packetlimit')
        if not packetlimit:
            # execute first limt command
            # TODO: limit command?
            tagobject.tags['packetlimit'] = '1'
        elif packetlimit == '1':
            # execute 2nd limit command
            # TODO: limit command?
            tagobject.tags['packetlimit'] = '2'
        elif packetlimit == '2':
            # lets nuke this vms
            dom = con.lookupByUUIDString(vm['referenceId'])
            dom.destroy()
            tagobject.tags['packetlimit'] = '3'
    if change:
        ccl.vmachine.updateSearch({'id': vm['id']}, {'$set': {'tags': tagobject.tagstring}})


def action():
    import libvirt
    ccl = j.clients.osis.getNamespace('cloudbroker')
    con = libvirt.open()
    domainguids = [dom.UUIString() for dom in con.listAllDomains()]
    vms = ccl.vmachine.search({'$query': {'referenceId': {'$in': domainguids}},
                               '$fields': ['tags', 'id', 'referenceId']
                               })[1:]
    vmdict = {vm['id']: vm for vm in vms}
    tmessage = {'state': 'OK', 'category': 'Network', 'message': 'All VM traffic is within boundries'}
    results = []

    nodekey = j.application.getAgentId()
    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    nicstats = dict()
    for stat in statsclient.statsByPrefix('network.packets'):
        nic = stat.tagObject.tagGet('nic')
        if nic.startswith('vm-'):
            nic = stat.tagObject.tagGet('nic')
            nicstats[nic] = nicstats.setdefault(nic, 0) + stat.m_last

    for nic, packetsin5min in nicstats.iteritems():
        packetsps = packetsin5min / float(300)
        message = tmessage.copy()
        message['message'] = 'VM nic {} has {:.2f} packets/s'.format(nic, packetsps)
        if packetsps > 10000:
            message['state'] = 'ERROR'
        elif packetsin5min > 8000:
            message['state'] = 'WARNING'

        if message['state'] != 'OK':
            results.append(message)

        vmid = int(nic.split('-')[1])
        tag_vm(ccl, vmdict.get(vmid), message['state'], con)

    if not results:
        results.append(tmessage)

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
