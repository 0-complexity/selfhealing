
# JumpScript: info_gather_cpu_ctxpy.py
        
#### category: monitor.healthcheck
#### queue: process
#### enable: True
#### descr: 
```
This healthcheck checks if amount of context switches per CPU is higher than expected.

Currently throws WARNING if more than 1M context switches and throws ERROR if more than 600k context switches

TODO : check these values, specifically if amount of cores per CPU is growing


```
#### license: bsd
#### author: deboeckj@codescalers.com
#### startatboot: True
#### scriptname: /opt/code/github/selfhealing/jumpscripts/healthchecks/info_gather_cpu_ctxpy.py
#### version: 1.0
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True