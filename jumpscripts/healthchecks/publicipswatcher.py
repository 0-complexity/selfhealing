from JumpScale import j

import netaddr

descr = """
Checks the status of the available public IPs.
Result will be shown in the "Network" section of the Grid Portal / Status Overview / Node Status page.
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
    pools = ccl.externalnetwork.search(query={})[1:]  # ignore the count of search result.

    for pool in pools:
        ips = pool['ips']
        ips_count = len(ips)
        usedips_count = ccl.cloudspace.count({'externalnetworkId': pool['id'], 'status': 'DEPLOYED'})
        for vm in ccl.vmachine.search({'nics.type': 'PUBLIC', 'status': {'$nin': ['ERROR', 'DESTROYED']}})[1:]:
            for nic in vm['nics']:
                if nic['type'] == 'PUBLIC':
                    tagObj = j.core.tags.getObject(nic['params'])
                    if int(tagObj.tags.get('externalnetworkId', '0')) == pool['id']:
                        usedips_count += 1

        percent = (float(usedips_count) / (usedips_count + ips_count)) * 100
        if percent > 95:
            results.append(dict(state='ERROR', category=category,
                                message="Used External IPs on {name} passed the dangerous threshold. ({percent:.0f}%)"
                                .format(name=pool['name'], percent=percent)))
        elif percent > 80:
            results.append(dict(state='WARNING', category=category,
                                message="Used External IPs on {name} passed the critical threshold. ({percent:.0f}%)"
                                .format(name=pool['name'], percent=percent)))

        else:
            results.append(dict(state='OK', category=category,
                                message="Used External IPs on {name} ({percent:.0f}%)"
                                .format(name=pool['name'], percent=percent)))

    return results

if __name__ == "__main__":
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
