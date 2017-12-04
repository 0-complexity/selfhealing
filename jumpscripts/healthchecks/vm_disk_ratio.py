from JumpScale import j
import time

descr = """
Check if number of disks exceeded 6 times machines
"""

organization = 'jumpscale'
name = 'vm_disk_ratio'
author = "foudaa@greenitglobe.com"
version = "1.0"
category = "monitor.healthcheck"
queue = 'process'
period = 3600 * 2  # 2 hrs
enable = False
async = True
roles = ['master', ]
log = False


def action(gid=None):
    result = dict()
    result['state'] = 'OK'
    result['category'] = 'healthcheck'
    result['uid'] = 'vm disk ratio'
    result['message'] = 'Disks number less than 6 times than machines number'

    cbcl = j.clients.osis.getNamespace('cloudbroker')
    vmachines_count = cbcl.vmachine.count()
    disks_count = cbcl.disk.count()
    if vmachines_count > 0 and  disks_count / vmachines_count >= 6:
        result['message'] = 'Disks number exceeded 6 times more than machines number'
        result['state'] = 'WARNING'
    return [result]


if __name__ == '__main__':
    action()
