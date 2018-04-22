from JumpScale import j

descr = """
This script creates an ovs cgroup and assig ovs related processes to it
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
roles = ['cpunode', 'storagedriver']
timeout = 60


def action():
    scl = j.clients.osis.getNamespace('system')
    grid = scl.grid.get(j.application.whoAmI.gid)
    ovslimits = grid.settings.get('limits', {}).get('ovs')
    if not ovslimits:
        return

    mem = ovslimits['memory'] # should be in Mega
    cpu = ovslimits['cpu']
    j.system.process.run('apt-get -y install cgroup-bin cgroup-lite cgroup-tools', showOutput=False, captureOutput=True, stopOnError=False)
    j.system.platform.cgroups.create('ovs')
    j.system.platform.cgroups.set_mem_limit('ovs', mem)
    j.system.platform.cgroups.set_cpu_cores('ovs', cpu)

    pids = []
    for name, status in j.system.platform.ubuntu.listServices().items():
        if status == 'enabled' and 'ovs' in name or 'arakoon' in name or 'alba' in name:
            pid = j.system.platform.ubuntu.getServicePID(name.strip())
            if pid:
                pids.append(pid)
    if pids:
        j.system.platform.cgroups.add_processes('ovs', pids)

if __name__ == '__main__':
    action()
