from JumpScale import j

descr = """
Checks for orphan disks on volume driver nodes. Generates warning if orphan disks exist on the specified volumes.
Result will be shown in the "Orphanage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
category = "monitor"
author = "deboeckj@codescalers.com"
version = "1.0"

enable = True
async = True
roles = ['storagedriver']
queue = 'process'


def action(deltatime=3600*24*7):
    import time
    import json
    import urlparse
    nid = j.application.whoAmI.nid
    gid = j.application.whoAmI.gid
    treshold = time.time() - deltatime

    scl = j.clients.osis.getNamespace('system')
    cbcl = j.clients.osis.getNamespace('cloudbroker', j.core.osis.client)
    ovs = scl.grid.get(j.application.whoAmI.gid).settings['ovs_credentials']
    ovscl = j.clients.openvstorage.get(ovs['ips'], (ovs['client_id'], ovs['client_secret']))
    DISK_FOUND = 'Deleting disk %s at %s'
    DISK_WITH_EDGE = 'Orphen disk: %s with connected edge'

    def get_devices(deviceurl):
        devices = []
        url = urlparse.urlparse(deviceurl.rsplit('@', 1)[0])
        device = url.path.split(':', 1)[0] + '.raw'
        devices.append(device)
        return devices

    def get_network_devices(networks):
        disks = {}
        for network in networks:
            # /mnt/vmstor/routeros/00ca/routeros-small-00ca.raw
            devicename = '/routeros/{0:04x}/routeros-small-{0:04x}.raw'.format(network['id'])
            disks[devicename] = 'DEPLOYED'
        return disks

    def get_cloud_inits(vms):
        disks = {}
        for vm in vms:
            devicename = '/vm-{id}/cloud-init-vm-{id}.raw'.format(id=vm['id'])
            disks[devicename] = 'DEPLOYED'
        return disks

    vcl = j.clients.osis.getNamespace('vfw', j.core.osis.client)
    disks = cbcl.disk.search({'$fields': ['status', 'referenceId'], '$query': {'gid': gid}}, size=0)[1:]
    # Map referenceIds and statuses
    diskmap = {}
    for disk in disks:
        for device in get_devices(disk['referenceId']):
            diskmap[device] = disk['status']
    networks = vcl.virtualfirewall.search({'$fields': ['id'], '$query': {'gid': j.application.whoAmI.gid}}, size=0)[1:]
    diskmap.update(get_network_devices(networks))
    vms = cbcl.vmachine.search({'$fields': ['id'],
                                '$query': {'status': {'$ne': 'DESTROYED'}}}, size=0)[1:]
    cloudinits = get_cloud_inits(vms)
    diskmap.update(cloudinits)
    results = []

    for disk in ovscl.get('/vdisks', params={'contents': 'devicename'})['data']:
        devicename = disk['devicename']
        if devicename.startswith('/templates'):
            continue
        elif devicename.startswith('/archive'):
            continue
        elif diskmap.get(disk['devicename'], 'DESTROYED') == 'DESTROYED':
            disk = ovscl.get('/vdisks/{}'.format(disk['guid']))
            edge_client = disk.get('edge_clients')
            if not edge_client:
                deletedisk = False
                snapshottime = 0
                for snapshot in disk['snapshots']:
                    if snapshot['label'] == 'orphan':
                        snapshottime = int(snapshot['timestamp'])
                        if snapshottime < treshold:
                            deletedisk = True
                        break
                if deletedisk:
                    print('Deleting {}'.format(disk['devicename']))
                    ovscl.delete('/vdisks/{}'.format(disk['guid']))
                    eco_tags = j.core.tags.getObject()
                    eco_tags.tagSet('vdiskGuid', disk['guid'])
                    eco_tags.labelSet('vdisk.delete')
                    eco_tags.labelSet('ovs.diskdelete')
                    j.errorconditionhandler.raiseOperationalWarning(
                        message='delete ovs disk %s on nid:%s gid:%s' % (disk['guid'], nid, gid),
                        category='selfhealing',
                        tags=str(eco_tags)
                    )
                    continue
                elif snapshottime == 0:
                    print('Adding snapshot marker')
                    snapshottime = int(time.time())
                    params = dict(name='orphan', timestamp=snapshottime, sticky=True)
                    ovscl.post('/vdisks/{}/create_snapshot'.format(disk['guid']), data=json.dumps(params))
                    eco_tags = j.core.tags.getObject()
                    eco_tags.tagSet('vdiskGuid', disk['guid'])
                    eco_tags.labelSet('vdisk.snapshot')
                    eco_tags.labelSet('ovs.snapshot')
                    j.errorconditionhandler.raiseOperationalWarning(
                        message='create snapshot of ovs disk %s on nid:%s gid:%s' % (disk['guid'], nid, gid),
                        category='selfhealing',
                        tags=str(eco_tags)
                    )
            else:
                results.append({'state': 'WARNING',
                    'category': 'Orphanage',
                    'message': DISK_WITH_EDGE % (disk['devicename']),
                    'uid': disk['devicename']
                    })
                continue
            results.append({'state': 'WARNING',
                            'category': 'Orphanage',
                            'message': DISK_FOUND % (disk['devicename'], "{{ts: %s}}" % (snapshottime + deltatime)),
                            'uid': disk['devicename']
                            })

    return results

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deltatime', type=int, default=3600*7*24, help='Time to keep orphans defaults to 7days, value is in seconds')
    options = parser.parse_args()
    j.core.osis.client = j.clients.osis.getByInstance('main')
    import yaml
    print(yaml.safe_dump(action(options.deltatime), default_flow_style=False))
