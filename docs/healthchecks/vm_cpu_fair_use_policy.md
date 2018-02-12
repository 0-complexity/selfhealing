
# JumpScript: vm_cpu_fair_use_policy.py
        
#### category: monitor.healthcheck
#### queue: process
#### enable: True
#### descr: 
```
Checks cpu time and quratines machine according to fair use policy .

If average per 5 min is higher than threshold a warning is sent via email.

if over use presists for longer than warntime  the machine is quarantined to a limit,
this is done for a quarantine time and then unquarantined .

if quarantined again after unquarantine quarantine time doubles for each time.

```
#### license: bsd
#### author: tareka@greenitglobe.com
#### startatboot: True
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/vm_cpu_fair_use_policy.py
#### version: 1.0
#### roles: ['cpunode']
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True