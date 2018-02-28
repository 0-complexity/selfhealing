from JumpScale import j

descr = """
This script executes btrfs balance command every 5 days at 4 in the morning random .
"""

organization = "jumpscale"
author = "support@gig.tech"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
interval = (2 * j.application.whoAmI.nid) % 30
period = "%s 4 */5 * *" % (interval)
startatboot = False
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['cpunode', 'storagenode', 'storagedriver', ]
timeout = 10


def action():
    j.system.process.execute('nohup /bin/btrfs balance start -dusage=80 / > /dev/null &', useShell=True, noDuplicates=True)


if __name__ == '__main__':
    action()
