
# JumpScript: ovs_disk_safety.py
        
#### category: disk.monitoring
#### enable: True
#### descr: 
```
Gathers statistics about disk safety and sends this disk safety statistics for each vpool and the amount of namespaces with the lowest disk safety to the database.

```
#### license: bsd
#### author: christophe@greenitglobe.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/collectors_stats/ovs_disk_safety.py
#### version: 1.0
#### roles: ['storagedriver']
#### async: True
#### organization: jumpscale
#### action_docstring: Send disk safety for each vpool and the amount of namespaces with the lowest disk safety to DB
#### order: 1
#### log: False