
# JumpScript: vm_orphan.py
        
#### category: monitor.healthcheck
#### enable: True
#### name: vm_orphan
#### descr: 
```
Checks if libvirt still has VMs that are not known by the system. These VMs are called orphan VMs. Takes into account VMs that have been moved to other CPU nodes.
If orphan disks exist, WARNING is shown in the "Orphanage" section of the Grid Portal / Status Overview / Node Status page.

```
#### author: deboeckj@codescalers.com
#### period: 3600
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/vm_orphan.py
#### version: 1.0
#### roles: ['cpunode']
#### async: True
#### organization: jumpscale
#### action_docstring: None