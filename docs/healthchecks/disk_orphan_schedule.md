
# JumpScript: disk_orphan_schedule.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['master']
#### descr: 
```
Scheduler that runs on master to check for orphan disks on specific volumedriver nodes

Generates warning if orphan disks exist on the specified volumes

```
#### author: deboeckj@codescalers.com
#### period: 3600
#### queue: process
#### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/disk_orphan_schedule.py
#### version: 1.0
#### async: True
#### organization: cloudscalers
#### action_docstring: None