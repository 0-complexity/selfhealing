
# JumpScript: cpu_ctxpy_check.py
        
#### category: monitor.healthcheck
#### queue: process
#### enable: True
#### descr: 
```
Checks the number of CPU context switches per second. If higher than expected an error condition is thrown.

Currently throws:
- WARNING if more than 1M context switches/s
- ERROR if more than 600k context switches/s

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.

TODO : check these values, specifically if amount of cores per CPU is growing

```
#### license: bsd
#### author: deboeckj@codescalers.com
#### startatboot: True
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/cpu_ctxpy_check.py
#### version: 1.0
#### roles: ['node']
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True