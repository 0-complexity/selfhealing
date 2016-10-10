
# JumpScript: network_virtual_stats.py
        
#### category: info.gather.nic
#### enable: True
#### descr: 
```
Gathers following network statistics from the virtual machines:
  - network.throughput.outgoing
  - network.throughput.incoming
  - network.packets.tx
  - network.packets.rx

```
#### license: bsd
#### author: deboeckj@codescalers.com
#### period: 60
#### queue: process
#### scriptname: /opt/code/github/0-complexity/selfhealing/jumpscripts/collectors_stats/network_virtual_stats.py
#### version: 1.0
#### roles: ['cpunode']
#### async: True
#### organization: jumpscale
#### action_docstring: None
#### log: False