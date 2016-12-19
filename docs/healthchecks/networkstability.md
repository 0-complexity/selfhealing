
# JumpScript: networkstability.py
        
#### category: monitor.healthcheck
#### enable: True
#### log: True
#### descr: 
```
Tests network between cpu and storage nodes
Make sure all types of network can reach eachother
Ping nodes for 10 times
When less then 90% produce a warning
When less then 70% procede an error
When timings are more then 10ms produce a warning
When timings are more then 100ms produce am error


```
#### author: deboeckj@greenitglobe.com
#### period: 300
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/networkstability.py
#### roles: ['storagenode', 'storagedriver', 'cpunode']
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### order: 1