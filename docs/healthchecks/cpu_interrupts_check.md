
# JumpScript: cpu_interrupts_check.py
        
#### category: monitor.healthcheck
#### license: bsd
#### enable: True
#### queue: process
#### descr: 
```
Checks the number of interrupts per second. If higher than expected an error condition is thrown.

Currently throws:
- WARNING if more than 8K interrupts/s
- ERROR if more than 10K interrupts/s

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.

```
#### roles: ['node']
#### author: christophe@greenitglobe.com
#### period: 60
#### startatboot: True
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/cpu_interrupts_check.py
#### version: 1.0
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True