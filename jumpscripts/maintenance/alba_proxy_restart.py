from JumpScale import j

descr = """
This script alba proxy restart command every days at 7 in the morning .
"""

organization = "jumpscale"
author = "support@gig.tech"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
interval = (2 * j.application.whoAmI.nid) % 30
period = "%s 7 * * *" % (interval)
startatboot = False
order = 1
enable = True
async = True
log = True
queue = 'process'
roles = ['storagenode']
timeout = 60 * 5


def action():
    for name, status in j.system.platform.ubuntu.listServices().items():
        if 'ovs-albaproxy' in name and status == 'enabled':
            print('Restarting {}'.format(name))
            j.system.platform.ubuntu.restartService(name)


if __name__ == '__main__':
    action()
