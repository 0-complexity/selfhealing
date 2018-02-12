
# JumpScript: ovs_healthcheck_short.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['storagedriver']
#### descr: 
```
Calls the standard Open vStorage health checks, see: https://github.com/openvstorage/openvstorage-health-check
Result will be shown in the "OpenvStorage" section of the Grid Portal / Status Overview / Node Status page.

```
#### author: foudaa@codescalers.com
#### period: 180
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/ovs_healthcheck_short.py
#### version: 1.0
#### timeout: 60
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### log: True