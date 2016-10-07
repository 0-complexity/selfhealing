from JumpScale import j

descr = """
Checks whether virtual firewall (RouterOS of cloud space) can reach its default gateway (public / private external IP@)
Result will be shown... WHERE?
"""

organization = 'cloudscalers'
author = "deboeckj@codescalers.com"
version = "1.0"
category = "monitor.vfw"
enable = True
async = True
log = False
roles = ['fw',]
queue = 'process'
period = 3600

def action():
    import JumpScale.grid.osis
    import netaddr
    import JumpScale.lib.routeros

    osiscl = j.clients.osis.getByInstance('main')
    vfwcl = j.clients.osis.getCategory(osiscl, 'vfw', 'virtualfirewall')
    cbcl = j.clients.osis.getNamespace('cloudbroker')

    pools = dict()

    def getDefaultGW(publicip):
        net = netaddr.IPNetwork(publicip)
        cidr = str(net.cidr)
        if cidr not in pools:
            pool = cbcl.publicipv4pool.get(cidr)
            pools[cidr] = pool

        return pools[cidr].gateway

    result = dict()
    cloudspaces = dict()
    def processCloudSpace(cloudspace):
        cloudspaceid = cloudspace['id']
        cloudspaces[cloudspaceid] = cloudspace
        if cloudspace['networkId']:
            gwip = getDefaultGW(cloudspace['publicipaddress'])
            try:
                vfw = vfwcl.get("%s_%s" % (j.application.whoAmI.gid, cloudspace['networkId']))
                if vfw.nid != j.application.whoAmI.nid:
                    return
                if j.system.net.tcpPortConnectionTest(vfw.host, 8728, 7):
                    routeros = j.clients.routeros.get(vfw.host, vfw.username, vfw.password)
                else:
                    result[cloudspaceid] = 'Could not connect to RouterOS %s' % vfw.host
                    return
            except Exception, e:
                result[cloudspaceid] = str(e)
                return
            if gwip:
                pingable = routeros.ping(gwip)
                if not pingable:
                    result[cloudspaceid] = 'Could not ping %s'  % gwip
            else:
                result[cloudspaceid] = 'No GW assigned'
    for cloudspace in cbcl.cloudspace.search({'gid': j.application.whoAmI.gid, 'status': 'DEPLOYED'})[1:]:
        print "Checking CloudspaceId: %(id)s NetworkId: %(networkId)s PUBIP: %(publicipaddress)s" % cloudspace
        processCloudSpace(cloudspace)
    if result:
        body = """
        Some virtual firewalls (VFW) have connection issues, please investigate
        """
        for cloudspaceid, message in result.iteritems():
            cloudspace = cloudspaces[cloudspaceid]
            body += "* CloudspaceId: %(id)s NetworkId: %(networkId)s PUBIP: %(publicipaddress)s\n" % cloudspace
            body += "  ** %s \n\n" % message

        j.errorconditionhandler.raiseOperationalWarning(body, 'monitoring')
        print body
    return result


if __name__ == '__main__':
    result = action()
    import yaml
    import json
    with open('/root/vfws_check.json', 'w') as fd:
        json.dump(result, fd)
    print yaml.dump(result)
