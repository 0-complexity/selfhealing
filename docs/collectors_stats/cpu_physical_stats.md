
# JumpScript: cpu_physical_stats.py
        
#### category: monitoring.processes
#### enable: True
#### descr: 
```
Gathers following CPU statistics from physical machines:
- CPU time
- CPU percent
- Number of threads
- Number of context switches
- Number of interrupts

Statistics are writen to Redis.

```
#### license: bsd
#### author: kristof@incubaid.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/collectors_stats/cpu_physical_stats.py
#### version: 1.0
#### roles: ['node']
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### log: False