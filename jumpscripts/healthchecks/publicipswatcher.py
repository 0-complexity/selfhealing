from JumpScale import j

import netaddr

descr = """
Checks the status of the available public IPs.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['master']
period = 1800 # 30mins.
enable = True
async = True
queue = 'process'
log = True


def action():
    category = "Network"
    results = []
    ccl = j.clients.osis.getNamespace('cloudbroker')
    pools = ccl.publicipv4pool.search(query={})[1:] #ignore the count of search result.

    for pool in pools:
        network = netaddr.IPNetwork(pool['id'])
        gid = pool['gid']
        pubips = pool['pubips']
        pubips_count = len(pubips)
        poolid = pool['id']
        usedips_count = ccl.cloudspace.count({'gid': gid, 'status': 'DEPLOYED'})
        for vm in ccl.vmachine.search({'nics.type': 'PUBLIC', 'status': {'$nin': ['ERROR', 'DESTROYED']}})[1:]:
            for nic in vm['nics']:
                if nic['type'] == 'PUBLIC' and netaddr.IPNetwork(nic['ipAddress']).ip in network:
                    usedips_count += 1


        critical = 0.8 < (float(usedips_count)/usedips_count+pubips_count) < 0.95
        dangerous = 0.95 < (float(usedips_count)/usedips_count+pubips_count)
        if critical:
            results.append(dict(state='WARNING', category=category, message="used public IPs on {poolid} passed the critical threshold. (80%)".format(poolid=poolid)))
        if dangerous:
            results.append(dict(state='ERROR', category=category, message="used public IPs on {poolid} passed the dangerous threshold. (95%)".format(poolid=poolid)))
    return results

if __name__ == "__main__":
    print action()
