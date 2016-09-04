
# JumpScript: /opt/code/github/selfhealing/jumpscripts/healthchecks/info_gather_workerstatus.py
        ### category: monitor.healthcheck
### descr: 
```
Monitors if WORKERS on regular basis report to the agent for new tasks.

Throws ERROR if WORKERS waits longer thane expected:
For Default queue > 2 mins
For IO queue > 2 hours
For Hypervisor queue > 10 mins
For Process queue > 1 min

```
### license: bsd
### author: khamisr@codescalers.com
### period: 600
### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/info_gather_workerstatus.py
### version: 1.0
### roles: []
### async: True
### organization: jumpscale
### action_docstring: None
### log: True
