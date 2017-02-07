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


def action():
    import time
    import json
    import urlparse
    nid = j.application.whoAmI.nid
    gid = j.application.whoAmI.gid
    deltatime = 3600 * 24 * 7
    treshold = time.time() - deltatime

    scl = j.clients.osis.getNamespace('system')
    cbcl = j.clients.osis.getNamespace('cloudbroker', j.core.osis.client)
    ovs = scl.grid.get(j.application.whoAmI.gid).settings['ovs_credentials']
    ovscl = j.clients.openvstorage.get(ovs['ips'], (ovs['client_id'], ovs['client_secret']))
    DISK_FOUND = 'Deleting disk %s at %s'

    def get_devices(deviceurl):
        devices = []
        url = urlparse.urlparse(deviceurl.rsplit('@', 1)[0])
        device = url.path + '.raw'
        devices.append(device)
        if 'bootdisk' in device:
            devices.append(device.replace('bootdisk', 'cloud-init'))
        return devices

    def get_network_devices(networks):
        disks = {}
        for network in networks:
            # /mnt/vmstor/routeros/00ca/routeros-small-00ca.raw
            devicename = '/routeros/{0:04x}/routeros-small-{0:04x}.raw'.format(network['id'])
            disks[devicename] = 'DEPLOYED'
        return disks

    vcl = j.clients.osis.getNamespace('vfw', j.core.osis.client)
    disks = cbcl.disk.search({'$fields': ['status', 'referenceId']}, size=0)[1:]
    # Map referenceIds and statuses
    diskmap = {}
    for disk in disks:
        for device in get_devices(disk['referenceId']):
            diskmap[device] = disk['status']
    networks = vcl.virtualfirewall.search({'$fields': ['id'], '$query': {'gid': j.application.whoAmI.gid}}, size=0)[1:]
    diskmap.update(get_network_devices(networks))

    results = []

    for disk in ovscl.get('/vdisks', params={'contents': 'devicename'})['data']:
        devicename = disk['devicename']
        if devicename.startswith('/templates'):
            continue
        elif devicename.startswith('/archive'):
            continue
        elif diskmap.get(disk['devicename'], 'DESTROYED') == 'DESTROYED':
            disk = ovscl.get('/vdisks/{}'.format(disk['guid']))
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
            results.append({'state': 'WARNING',
                            'category': 'Orphanage',
                            'message': DISK_FOUND % (disk['devicename'], "{{ts: %s}}" % (snapshottime + deltatime)),
                            'uid': disk['devicename']
                            })

    return results

if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
