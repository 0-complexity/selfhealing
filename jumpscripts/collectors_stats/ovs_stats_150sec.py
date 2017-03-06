from JumpScale import j

descr = """
Scheduler that runs on controller to collect OpenvStorage stats
"""

organization = 'greenitglobe'
author = "deboeckj@codescalers.com"
version = "1.0"

enable = True
async = True
period = 180  # 3minutes
roles = ['controller']
queue = 'process'
log = False


def action():
    acl = j.clients.agentcontroller.get()
    acl.executeJumpscript('greenitglobe', 'ovs_vdisks', role='storagemaster', gid=j.application.whoAmI.gid, wait=False)


if __name__ == '__main__':
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()
