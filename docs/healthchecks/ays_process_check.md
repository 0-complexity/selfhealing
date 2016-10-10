
# JumpScript: ays_process_check.py
        
#### category: monitor.healthcheck
#### enable: True
#### descr: 
```
Checks if all AYS processes are running.
Throws an error condition for each process that is not running.
Result will be shown in the "AYS Process" section of the Grid Portal / Status Overview / Node Status page.

```
#### license: bsd
#### author: deboeckj@codescalers.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/ays_process_check.py
#### version: 1.0
#### roles: ['node']
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True