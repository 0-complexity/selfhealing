from JumpScale import j

descr = """
Scheduler that runs on controller to check for disks/vms ratio
Generates warning if number of disks reached 6 times or more than number of machines.
"""

organization = 'cloudscalers'
category = "monitor.healthcheck"
author = "foudaa@greenitglobe.com"
version = "1.0"

enable = True
async = True
period = "30 * * * *"
timeout = 3600
roles = ['controller', ]
queue = 'process'


def action():
    acl = j.clients.agentcontroller.get()
    results = []
    job = acl.executeJumpscript('cloudscalers', 'vm_disk_ratio', role='storagedriver', gid=j.application.whoAmI.gid)
    if job['state'] == 'OK':
        results.extend(job['result'])

    if not results:
        results.append({'state': 'OK', 'category': 'VMs-Disks ratio', 'message': 'disks/vms ratio is OK.'})
    return results


if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print(action())
