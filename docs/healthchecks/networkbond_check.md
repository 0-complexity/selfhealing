
# JumpScript: networkbond_check.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['node']
#### descr: 
```
Monitors if a network bond (if there is one) has both (or more) interfaces properly active.
Problems are reported in the "Hardware" section of the Grid Portal / Status Overview / Node Status page.

```
#### author: deboeckj@greenitglobe.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/networkbond_check.py
#### version: 1.0
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### log: True