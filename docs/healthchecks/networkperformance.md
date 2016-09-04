
# JumpScript: /opt/code/github/selfhealing/jumpscripts/healthchecks/networkperformance.py
        ### category: monitor.healthcheck
### enable: False
### log: True
### descr: 
```
Tests bandwidth between storage nodes, volume drivers and itself (CPU Node)

Generates a warning if bandwidth is below 50% of the maximum speed
Generates an error if bandwidth is below 10% of the maximum speed


```
### author: hamdy.farag@codescalers.com
### queue: io
### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/networkperformance.py
### roles: ['storagenode']
### async: True
### organization: cloudscalers
### action_docstring: None
### order: 1
