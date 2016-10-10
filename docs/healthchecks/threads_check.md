
# JumpScript: threads_check.py
        
#### category: monitor.healthcheck
#### queue: process
#### enable: True
#### descr: 
```
Checks the number of threads, and throw an error if higher than expected.

Currently throws
- WARNING if more than 18K threads
- ERROR if more than 20K threads

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.

```
#### license: bsd
#### author: christophe@greenitglobe.com
#### startatboot: True
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/healthchecks/threads_check.py
#### version: 1.0
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### order: 1
#### log: True