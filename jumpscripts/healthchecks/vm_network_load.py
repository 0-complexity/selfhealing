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
timeout = 60

WARNING_TRESHHOLD = 8000
ERROR_TRESHHOLD = 10000


def tag_vm(ccl, vm, state, con):
    nid = j.application.whoAmI.nid
    gid = j.application.whoAmI.gid
    ccl = j.clients.osis.getNamespace('cloudbroker')
    if vm is None:
        return  # vm has left this node
    tagobject = j.core.tags.getObject(vm['tags'])
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
            cloudspace = ccl.cloudspace.get(vm['cloudspaceId'])
            eco_tags = j.core.tags.getObject()
            eco_tags.tagSet('machineId', dom.name())
            eco_tags.tagSet('accountId', cloudspace.accountId)
            eco_tags.tagSet('cloudspaceId', cloudspace.id)
            eco_tags.labelSet('domain.destroy')
            eco_tags.labelSet('vm.delete')
            j.errorconditionhandler.raiseOperationalWarning(
                message='destroy domain %s for excess bandwidth consumption on nid:%s gid:%s' % (dom.name(), nid, gid),
                category='selfhealing',
                tags=str(eco_tags)
            )
    if change:
        print 'Tagging VM {} {}'.format(vm['id'], str(tagobject))
        ccl.vmachine.updateSearch({'id': vm['id']}, {'$set': {'tags': str(tagobject)}})


def action():
    import libvirt
    ccl = j.clients.osis.getNamespace('cloudbroker')
    con = libvirt.open()
    domainguids = [dom.UUIDString() for dom in con.listAllDomains()]
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
        message['uid'] = 'VM_nic_load:{}'.format(nic)
        if packetsps > ERROR_TRESHHOLD:
            message['state'] = 'ERROR'
        elif packetsps > WARNING_TRESHHOLD:
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
