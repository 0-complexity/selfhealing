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
timeout = 60


def action():
    acl = j.clients.agentcontroller.get()
    acl.executeJumpscript('greenitglobe', 'disk_garbage_collector', role='storagedriver', gid=j.application.whoAmI.gid, wait=False)

if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()
