
# JumpScript: disk_orphan.py
        
#### category: monitor
#### enable: True
#### roles: ['storagedriver']
#### descr: 
```
Checks for orphan disks on volume driver nodes. Generates warning if orphan disks exist on the specified volumes.
Result will be shown in the "Orphanage" section of the Grid Portal / Status Overview / Node Status page.

```
#### author: deboeckj@codescalers.com
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/disk_orphan.py
#### version: 1.0
#### async: True
#### organization: cloudscalers
#### action_docstring: None