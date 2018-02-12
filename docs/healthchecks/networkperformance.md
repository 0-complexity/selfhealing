
# JumpScript: networkperformance.py
        
#### category: monitor.healthcheck
#### enable: False
#### log: True
#### descr: 
```
Tests bandwidth between storage nodes, volume drivers and itself

Generates a warning if bandwidth is below 50% of the maximum speed
Generates an error if bandwidth is below 10% of the maximum speed


```
#### author: deboeckj@greenitglobe.com
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/networkperformance.py
#### roles: ['storagenode', 'storagedriver', 'cpunode']
#### timeout: 60
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### order: 1