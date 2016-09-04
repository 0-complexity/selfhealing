
# JumpScript: /opt/code/github/selfhealing/jumpscripts/healthchecks/deployment_test.py
        ### category: monitor.healthcheck
### enable: True
### roles: ['cpunode']
### descr: 
```
Tests every period if test VM exists and if exists it test write speed.
Every 24hrs, test VM is recreated

Generates warning if write speed is lower than 50 MiB / second


```
### author: deboeckj@codescalers.com
### queue: io
### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/deployment_test.py
### version: 1.0
### async: True
### organization: cloudscalers
### action_docstring: None
### log: True
