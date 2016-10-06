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


def action(delete=False):
    import os
    import glob
    import time
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
        NETWORK_FOUND = 'Found orphan network disk %s'
        DISK_FOUND_CLOUD = 'Found orphan cloud-init %s'

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
            msg = None
            if file_.endswith('.raw'):
                if 'routeros' in file_:
                    networkid = int(os.path.basename(folder), 16)
                    if networkid not in activenetworks:
                        msg = NETWORK_FOUND
                elif file_.startswith('cloud-init'):
                    if len(files) == 1:
                        stat = os.stat(fullpath)
                        # check if file is older then 5min (might be basevolume is not created yet)
                        if stat.st_ctime < time.time() - 300:
                            msg = DISK_FOUND_CLOUD
                        else:
                            continue
                    else:
                        continue
                else:
                    diskstatus = diskmap.get(fullpath, 'DESTROYED')
                    if diskstatus == 'DESTROYED':
                        msg = DISK_FOUND
                if msg is not None:
                    print('Orphan disk %s' % fullpath)
                    if delete is True:
                        os.remove(fullpath)
                    else:
                        results.append({'state': 'WARNING',
                                        'category': 'Orphanage',
                                        'message': msg % fullpath,
                                        'uid': fullpath
                                        })

        if not files and not folder.endswith('/volumes'):
            os.rmdir(folder)

    for store in disks_paths():
        os.path.walk(store, process, None)

    return results

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delete', default=False, action='store_true')
    options = parser.parse_args()
    j.core.osis.client = j.clients.osis.getByInstance('main')
    action(options.delete)
