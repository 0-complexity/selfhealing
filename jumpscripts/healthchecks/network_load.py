from JumpScale import j
import netaddr
import math
import random

descr = """
Check the bandwith consumption of the network
"""
organization = "cloudscalers"
author = "deboeckj@greenitglobe.com"
order = 1
enable = True
async = True
log = True
queue = 'process'
period = 180
roles = ['storagenode', 'storagedriver', 'cpunode']
category = "monitor.healthcheck"


def action():
    tmessage = {'state': 'OK', 'category': 'Network'}
    results = []

    nodekey = j.application.getAgentId()
    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    for stat in statsclient.statsByPrefix('network.throughput'):
        nic = stat.tagObject.tagGet('nic')
        direction = stat.key.split('@')[0].split('.')[2]
        message = tmessage.copy()
        try:
            nicspeed = j.system.net.getNicSpeed(nic) / 8.  # nic speed is expressed in mbit but we want mbytes
        except:
            continue

        results.append(message)
        percent = (stat.m_last / float(nicspeed)) * 100
        message['message'] = 'Nic {} {} bandwith is {:.2f}%'.format(nic, direction, percent)
        if percent > 80:
            message['state'] = 'WARNING'
        elif percent > 90:
            message['state'] = 'ERROR'

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
