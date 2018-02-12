
# JumpScript: rabbitmq_restart.py
        
#### category: monitor.healthcheck
#### enable: True
#### roles: ['storagedriver']
#### descr: 
```
Check if there are partition issues in RabbitMQ. If issues were found it will restart RabbitMQ. 

```
#### author: chaddada@greenitglobe.com
#### period: 1800
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/maintenance/rabbitmq_restart.py
#### version: 1.0
#### timeout: 180
#### async: True
#### organization: cloudscalers
#### action_docstring: None
#### log: True