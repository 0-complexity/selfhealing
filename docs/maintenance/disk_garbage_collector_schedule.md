
# JumpScript: disk_garbage_collector_schedule.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['controller']
#### descr: 
```
Scheduler that runs on controller to check for orphan disks on specific volume driver nodes.
Generates warning if orphan disks exist on the specified volumes.

```
#### author: geert@greenitglobe.com
#### period: 3600
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/maintenance/disk_garbage_collector_schedule.py
#### version: 1.0
#### timeout: 60
#### async: True
#### organization: greenitglobe
#### action_docstring: None