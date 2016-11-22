from JumpScale import j
import netaddr
import math
import random
import json
import re
from fabric.network import NetworkError

descr = """
Tests network between cpu and storage nodes
Make sure all types of network can reach eachother

"""
organization = "cloudscalers"
author = "deboeckj@greenitglobe.com"
order = 1
enable = True
async = True
log = True
queue = 'process'
period = 300
roles = ['storagenode', 'storagedriver', 'cpunode']
category = "monitor.healthcheck"


def updateNetwork(node, networks):
    for netinfo in node:
        if netinfo['name'] == 'lo':
            continue
        for ip, cidr in zip(netinfo['ip'], netinfo['cidr']):
            net = netaddr.IPNetwork('{}/{}'.format(ip, cidr)).cidr
            networks.setdefault(net, []).append(ip)
    return networks


def ping(ip):
    return j.system.net.pingMachine(ip, 5), ip


def action():
    from multiprocessing import Pool
    scl = j.clients.osis.getNamespace('system')
    nodes = scl.node.search({'gid': j.application.whoAmI.gid, 'active': True, 'roles': {'$in': roles}})[1:]
    networks = {}
    results = []
    for node in nodes:
        if node['id'] != j.application.whoAmI.nid:
            updateNetwork(node['netaddr'], networks)

    for netinfo in j.system.net.getNetworkInfo():
        if netinfo['name'] == 'lo':
            continue
        for myip, cidr in zip(netinfo['ip'], netinfo['cidr']):
            mynet = netaddr.IPNetwork('{}/{}'.format(myip, cidr)).cidr
            netresults = []
            iplist = networks.get(mynet)
            if iplist is not None:

                pinglist = random.sample(iplist, int(math.log(len(iplist)) + 1))
                pool = Pool(len(pinglist))
                failures = []
                for result, ip in pool.map(ping, pinglist):
                    if not result:
                        failures.append(ip)
                if failures:
                    netresults.append({'message': 'Failed to reach {} from {}'.format(','.join(failures), myip), 'state': 'ERROR', 'category': 'Network'})
                else:
                    netresults.append({'message': 'Network {} ({}) reachable'.format(mynet, netinfo['name']), 'state': 'OK', 'category': 'Network'})
            else:
                netresults.append({'message': 'Found IP {} ({}) in strange network'.format(myip, netinfo['name']), 'state': 'WARNING', 'category': 'Network'})
            results.extend(netresults)

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
