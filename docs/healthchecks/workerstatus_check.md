
# JumpScript: workerstatus_check.py
        
#### category: monitor.healthcheck
#### descr: 
```
Monitors the workers, checking if they report back on regular basis report to their agent for new tasks.

Throws ERROR if WORKERS waits longer than expected:
For Default queue > 2 mins
For IO queue > 2 hours
For Hypervisor queue > 10 mins
For Process queue > 1 min

```
#### license: bsd
#### author: khamisr@codescalers.com
#### period: 600
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/workerstatus_check.py
#### version: 1.0
#### roles: ['node']
#### timeout: 60
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### log: True