from JumpScale import j

descr = """
Scheduler that runs on controller to check for orphan disks on specific volume driver nodes.
Generates warning if orphan disks exist on the specified volumes.
"""

organization = 'greenitglobe'
category = "monitor.healthcheck"
author = "geert@greenitglobe.com"
version = "1.0"

enable = True
async = True
period = 3600  # 1 hrs
roles = ['controller', ]
queue = 'process'


def action():
    acl = j.clients.agentcontroller.get()

    results = []
    job = acl.executeJumpscript('greenitglobe', 'disk_garbage_collector', role='storagedriver', gid=j.application.whoAmI.gid)
    if job['state'] == 'OK':
        results.extend(job['result'])

    if not results:
        results.append({'state': 'OK', 'category': 'GarbageCollector', 'message': 'Nothing needed to be cleaned.'})
    return results

if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()
