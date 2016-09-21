from JumpScale import j

descr = """
Checks on volumedriver node for orphan disks

Generates warning if orphan disks exist on the specified volumes
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
    import os
    import glob
    from CloudscalerLibcloud import openvstorage
    cbcl = j.clients.osis.getNamespace('cloudbroker', j.core.osis.client)
    vcl = j.clients.osis.getNamespace('vfw', j.core.osis.client)
    disks = cbcl.disk.search({'$fields': ['status', 'referenceId']}, size=0)[1:]
    # Map referenceIds and statuses
    diskmap = {openvstorage.getPath(disk['referenceId']): disk['status'] for disk in disks}
    networks = vcl.virtualfirewall.search({'$fields': ['id'], '$query': {'gid': j.application.whoAmI.gid}}, size=0)[1:]
    activenetworks = [network['id'] for network in networks]
    results = []

    def disks_paths():
        result = glob.glob('/mnt/data*/volumes')
        result.append('/mnt/vmstor')
        return result

    def process(_, folder, files):
        # Predefined messages
        DISK_FOUND = 'Found orphan disk %s'
        DISK_FOUND_CLOUD = 'Found orphan cloud-init %s'
        EMPTY_FOLDER = 'Found empty folder %s'

        # Ignore templates and archive files
        if 'templates' in files:
            files.remove('templates')
        if 'archive' in files:
            files.remove('archive')

        for file_ in files:
            # Ignore ovs-healthcheck-test* files
            if file_.startswith('ovs-healthcheck-test'):
                continue

            fullpath = os.path.join(folder, file_)
            if file_.endswith('.raw'):
                if 'routeros' in file_:
                    networkid = int(os.path.basename(folder), 16)
                    if networkid not in activenetworks:
                        results.append({
                                            'state': 'WARNING',
                                            'category': 'Orphanage',
                                            'message': DISK_FOUND % fullpath,
                                            'uid': fullpath
                                        })
                elif file_.startswith('cloud-init') and len(files) == 1:
                    results.append({
                                        'state': 'WARNING',
                                        'category': 'Orphanage',
                                        'message': DISK_FOUND_CLOUD % fullpath,
                                        'uid': fullpath
                                    })
                else:
                    diskstatus = diskmap.get(fullpath, 'DESTROYED')
                    if diskstatus == 'DESTROYED':
                        results.append({
                                            'state': 'WARNING',
                                            'category': 'Orphanage',
                                            'message': DISK_FOUND % fullpath,
                                            'uid': fullpath
                                        })
        if not files:
            results.append({
                                'state': 'WARNING',
                                'category': 'Orphanage',
                                'message': EMPTY_FOLDER % folder,
                                'uid': folder
                            })

    for store in disks_paths():
        os.path.walk(store, process, None)

    return results

if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()
