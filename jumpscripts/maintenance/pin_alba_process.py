from JumpScale import j

descr = """
This script pins alba-asd process to the reserved free processes
"""

organization = "jumpscale"
author = "foudaa@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
period = "0 * * * *"
startatboot = False
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['cpunode']


def action():
    from CloudscalerLibcloud.utils.libvirtutil import  RESERVED_CPUS
    for name, status in j.system.platform.ubuntu.listServices().items():
        if 'alba-asd' in name and status == 'enabled':
            pid = j.system.platform.ubuntu.getServicePID(name.strip())
            if pid:
                j.system.process.execute('taskset -pc 0-{reserved_cpus} {pid}'.format(reserved_cpus=RESERVED_CPUS-1, pid=pid))



if __name__ == '__main__':
    action()
