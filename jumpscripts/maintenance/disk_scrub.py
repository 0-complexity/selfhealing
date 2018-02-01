from JumpScale import j

descr = """
For each available vdisk it will perform a scrub on it if the stored size is three times bigger than the vdisk size.
"""

organization = 'greenitglobe'
category = "monitor.maintenance"
author = "chaddada@greenitglobe.com"
version = "1.0"
enable = True
async = True
roles = ['storagedriver']
queue = 'process'


def action():
    results = []
    scl = j.clients.osis.getNamespace('system', j.core.osis.client)
    ovs = scl.grid.get(j.application.whoAmI.gid).settings['ovs_credentials']
    ovscl = j.clients.openvstorage.get(ovs['ips'], (ovs['client_id'], ovs['client_secret']))
    for diskguid in ovscl.get('/vdisks')['data']:
        disk = ovscl.get('/vdisks/{}'.format(diskguid))
        print "Checking disk %s" % disk['devicename']
        if disk['info']['stored'] >= 3 * disk['size']:
            results.append({'state': 'WARNING', 'category': category, 'uid': disk['devicename'], 'message': 'disk storage exceeds allowed limit, scrubbing will be performed'})
            print "Scrubbing disk %s" % disk['devicename']
            ovscl.post('/vdisks/{}/scrub'.format(diskguid))
        else:
            results.append({'state': 'OK', 'category': category, 'uid': disk['devicename'], 'message': 'disk storage ok relative to disk size'})
    return results

if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    import yaml
    print yaml.dump(action())
