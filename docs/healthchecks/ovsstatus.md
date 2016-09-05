
# JumpScript: ovsstatus.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['storagenode']
#### descr: 
```
Checks every defined period if all OVS processes still run

Shows WARNING if process not running anymore


```
#### author: khamisr@codescalers.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/ovsstatus.py
#### version: 1.0
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### log: True