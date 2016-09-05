
# JumpScript: info_gather_cpu_mem_core.py
        
#### category: monitor.healthcheck
#### queue: process
#### enable: True
#### descr: 
```
This healthcheck checks if memory and CPU usage on average over 1hr per CPU is higher than expected.

For both memory and CPU usage throws WARNING if more than 80% used and throws ERROR if more than 95% used


```
#### license: bsd
#### author: deboeckj@codescalers.com
#### startatboot: True
#### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/info_gather_cpu_mem_core.py
#### version: 1.0
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True