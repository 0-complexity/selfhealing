
# JumpScript: cpu_mem_core_check.py
        
#### category: monitor.healthcheck
#### queue: process
#### enable: True
#### descr: 
```
Checks average memory and CPU usage/load. If average per hour is higher than expected an error condition is thrown.

For both memory and CPU usage throws WARNING if more than 80% used and throws ERROR if more than 95% used.

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.

```
#### license: bsd
#### author: deboeckj@codescalers.com
#### startatboot: True
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/cpu_mem_core_check.py
#### version: 1.0
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True