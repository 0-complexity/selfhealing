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
period = 1800  # 30mins.
enable = True
async = True
queue = 'process'
log = True


def action():
    category = "Network"
    results = []
    ccl = j.clients.osis.getNamespace('cloudbroker')
    pools = ccl.publicipv4pool.search(query={})[1:]  # ignore the count of search result.

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

        percent = (float(usedips_count) / (usedips_count + pubips_count)) * 100
        if percent > 95:
            results.append(dict(state='ERROR', category=category,
                                message="Used public IPs on {poolid} passed the dangerous threshold. ({percent:.0f}%)"
                                .format(poolid=poolid, percent=percent)))
        elif percent > 80:
            results.append(dict(state='WARNING', category=category,
                                message="Used public IPs on {poolid} passed the critical threshold. ({percent:.0f}%)"
                                .format(poolid=poolid, percent=percent)))

        else:
            results.append(dict(state='OK', category=category,
                                message="Used public IPs on {poolid} ({percent:.0f}%)"
                                .format(poolid=poolid, percent=percent)))

    return results

if __name__ == "__main__":
    print action()
