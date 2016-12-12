from JumpScale import j

descr = """
Scheduler that runs on controller to collect OpenvStorage stats
"""

organization = 'greenitglobe'
author = "deboeckj@codescalers.com"
version = "1.0"

enable = True
async = True
period = 60  # 1 hrs
roles = ['controller', ]
queue = 'process'


def action():
    acl = j.clients.agentcontroller.get()
    acl.executeJumpscript('greenitglobe', 'ovs_asd', role='storagemaster', gid=j.application.whoAmI.gid, wait=False)
    acl.executeJumpscript('greenitglobe', 'ovs_backend', role='storagemaster', gid=j.application.whoAmI.gid, wait=False)
    acl.executeJumpscript('greenitglobe', 'ovs_disk_safety', role='storagemaster',
                          gid=j.application.whoAmI.gid, wait=False)
    acl.executeJumpscript('greenitglobe', 'ovs_vpool', role='storagemaster', gid=j.application.whoAmI.gid, wait=False)


if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()
