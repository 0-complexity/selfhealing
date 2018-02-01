from JumpScale import j

descr = """
Scheduler that runs on controller to check for orphan disks on specific volume driver nodes.
Generates warning if orphan disks exist on the specified volumes.
"""

organization = 'cloudscalers'
category = "monitor.healthcheck"
author = "deboeckj@codescalers.com"
version = "1.0"

enable = True
async = True
period = "30 3 * * *"
timeout = 3600
roles = ['controller', ]
queue = 'process'


def action():
    acl = j.clients.agentcontroller.get()

    results = []
    job = acl.executeJumpscript('cloudscalers', 'disk_orphan', role='storagedriver', gid=j.application.whoAmI.gid)
    if job['state'] != 'OK':
        results.append({'state': 'ERROR', 'category': 'Orphanage', 'message': 'disk_orphan healthcheck failed check [job | job?id=%s]' % job['guid']})
    else:
        results.extend(job['result'])

    if not results:
        results.append({'state': 'OK', 'category': 'Orphanage', 'message': 'No orphan disks found.'})
    return results


if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print(action())
