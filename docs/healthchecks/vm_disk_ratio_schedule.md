
# JumpScript: vm_disk_ratio_schedule.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['controller']
#### descr: 
```
Scheduler that runs on controller to check for disks/vms ratio
Generates warning if number of disks reached 6 times or more than number of machines.

```
#### author: foudaa@greenitglobe.com
#### period: 30 * * * *
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/vm_disk_ratio_schedule.py
#### version: 1.0
#### timeout: 60
#### async: True
#### organization: cloudscalers
#### action_docstring: None