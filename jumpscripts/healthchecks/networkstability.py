from JumpScale import j
import netaddr
import math
import random

descr = """
Tests network between cpu and storage nodes
Make sure all types of network can reach eachother
Ping nodes for 10 times
When less then 90% produce a warning
When less then 70% procede an error
When timings are more then 10ms produce a warning
When timings are more then 200ms produce am error

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
    # first wake up the network
    j.system.net.ping(ip, 5)
    # check results
    pingresults = j.system.net.ping(ip)
    status = 'OK'
    percent = pingresults['percent']
    avg = pingresults.get('avg', -1)
    msg = 'Pingtest to {} successfull'.format(ip)
    if percent < 70:
        status = 'ERROR'
    elif status < 90:
        status = 'WARNING'
    if avg > 10:
        status = 'WARNING'
    elif avg > 200:
        status = 'ERROR'
    msg = 'Ping to {} {}% with average of {} ms'.format(ip, percent, avg if avg != -1 else 'NA')
    return {'message': msg, 'state': status, 'category': 'Network'}


def action():
    from multiprocessing import Pool
    from threading import Thread
    scl = j.clients.osis.getNamespace('system')
    nodes = scl.node.search({'gid': j.application.whoAmI.gid, 'active': True, 'roles': {'$in': roles}})[1:]
    networks = {}
    results = []
    for node in nodes:
        if node['id'] != j.application.whoAmI.nid:
            updateNetwork(node['netaddr'], networks)

    def process_network(netinfo):
        if netinfo['name'] == 'lo':
            return
        for myip, cidr in zip(netinfo['ip'], netinfo['cidr']):
            mynet = netaddr.IPNetwork('{}/{}'.format(myip, cidr)).cidr
            netresults = []
            iplist = networks.get(mynet)
            if iplist is not None:
                pool = Pool()
                pinglist = random.sample(iplist, int(math.log(len(iplist)) + 1))
                for result in pool.map(ping, pinglist):
                    netresults.append(result)
            else:
                netresults.append({'message': 'Found IP {} ({}) in strange network'.format(
                    myip, netinfo['name']), 'state': 'WARNING', 'category': 'Network'})
            results.extend(netresults)

    threads = []
    for netinfo in j.system.net.getNetworkInfo():
        thread = Thread(target=process_network, args=(netinfo,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
