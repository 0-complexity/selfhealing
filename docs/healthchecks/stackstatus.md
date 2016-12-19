
# JumpScript: stackstatus.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['cpunode']
#### descr: 
```
Checks the status of each stack (CPU node).

ERROR state is automatically attributed to a stack by OpenvCloud - this is done if a specific action cannot be executed anymore on the CPU Node.

Result will be shown in the "Stack Status" section of the Grid Portal / Status Overview / Node Status page.

```
#### author: deboeckj@codescalers.com
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/stackstatus.py
#### version: 1.0
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### log: True