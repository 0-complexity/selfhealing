from JumpScale import j

descr = """
This script executes drop caches, releasing buffered memory back to the system, every days at 2 in the morning + random seed .
"""

organization = "jumpscale"
author = "support@gig.tech"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
interval = (2 * j.application.whoAmI.nid) % 30
period = "%s */2 * * *" % (interval)
startatboot = False
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['cpunode', 'storagenode', 'storagedriver', ]


def action():
    j.system.process.execute('/bin/echo 3 > /proc/sys/vm/drop_caches &', useShell=True)


if __name__ == '__main__':
    action()

