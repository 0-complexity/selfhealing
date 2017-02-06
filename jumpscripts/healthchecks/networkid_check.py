from JumpScale import j

descr = """
Checks the status of the available networkids.
Result will be shown in the "Network" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "deboeckj@greenitglobe.com"
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
    lcl = j.clients.osis.getNamespace('libvirt')

    for location in ccl.location.search({})[1:]:
        gid = location['gid']
        if not lcl.networkids.exists(gid):
            results.append(dict(state='ERROR', category=category,
                                message="No networkids defined for gid {}".format(gid)))
        netids = len(lcl.networkids.get(gid).networkids)
        usedids_count = ccl.cloudspace.count({'gid': gid, 'status': {'$ne': 'DESTROYED'}})

        percent = (float(usedids_count) / (usedids_count + netids)) * 100
        message = "Used networkids on location {locationname} passed the dangerous threshold. ({percent:.0f}%)"
        state = 'OK'
        if percent > 95:
            state = 'ERROR'
        elif percent > 80:
            state = 'WARNING'
        else:
            message = "Used networkids on location {locationname} {percent:.0f}%"
        results.append(dict(state=state, category=category, message=message.format(locationname=location['name'], percent=percent)))

    return results

if __name__ == "__main__":
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
