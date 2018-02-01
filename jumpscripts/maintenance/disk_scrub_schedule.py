from JumpScale import j

descr = """
Scheduler that runs on controller that executes the disk_scrub script to scrub disk with more storage than their specified size.
"""

organization = 'greenitglobe'
category = "monitor.maintenance"
author = "chaddada@greenitglobe.com"
version = "1.0"

enable = True
async = True
period = "0 22 * * *" # Once per day at 22:00
roles = ['controller']
queue = 'process'
timeout = 60


def action():
    acl = j.clients.agentcontroller.get()
    acl.executeJumpscript('greenitglobe', 'disk_scrub', role='storagedriver', gid=j.application.whoAmI.gid, wait=False)

if __name__ == '__main__':
    action()
