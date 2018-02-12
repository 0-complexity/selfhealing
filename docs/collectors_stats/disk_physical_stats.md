
# JumpScript: disk_physical_stats.py
        
#### category: disk.monitoring
#### enable: True
#### descr: 
```
Gathers following statistics about the physical disks:
- time_read
- time_write
- count_read
- count_write
- kbytes_read
- kbytes_write
- MB_read
- MB_write
- space_free_mb
- space_used_mb
- space_percent

```
#### license: bsd
#### author: kristof@incubaid.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/collectors_stats/disk_physical_stats.py
#### version: 1.0
#### roles: ['node']
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: False