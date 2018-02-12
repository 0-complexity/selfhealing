
# JumpScript: disk_scrub_schedule.py
        
#### category: monitor.maintenance
#### enable: True
#### roles: ['controller']
#### descr: 
```
Scheduler that runs on controller that executes the disk_scrub script to scrub disk with more storage than their specified size.

```
#### author: chaddada@greenitglobe.com
#### period: 0 22 * * *
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/maintenance/disk_scrub_schedule.py
#### version: 1.0
#### timeout: 60
#### async: True
#### organization: greenitglobe
#### action_docstring: None