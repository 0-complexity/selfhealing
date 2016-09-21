from JumpScale import j
from gevent.pool import Pool


descr = """
Checks the status of RouterOS.
"""
organization = 'greenitglobe'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor"
roles = ['cpunode']
enable = True
async = True
queue = 'process'
log = True


def action():
    category = "Network"
    ccl = j.clients.osis.getNamespace('cloudbroker')
    cloudspaces = ccl.cloudspace.simpleSearch({'status': 'DEPLOYED'})

    def checkros(c):
        vcl = j.clients.osis.getNamespace('vfw')
        vfwid = '{gid}_{networkId}'.format(gid=c['gid'], networkId=c['networkId'])
        if not vcl.virtualfirewall.exists(vfwid):
            return dict(state='ERROR', category=category, message="RouterOS doesn't exist on {vfwid} {csname}".format(vfwid=vfwid, csname=c['name']))
        vfw = vcl.virtualfirewall.get(vfwid)
        try:
            client = j.clients.routeros.get(vfw.host, vfw.username, vfw.password)
            ok = client.ping('8.8.8.8')
            if not ok:
                return dict(state='ERROR', category=category, message="Couldn't ping 8.8.8.8 {vfwid} {csname}".format(vfwid=vfwid, csname=c['name']))
            return None
        except:
            return dict(state='ERROR', category=category, message="RouterOS died on {vfwid} {csname}".format(vfwid=vfwid, csname=c['name']))

    pool = Pool(10)
    results = pool.map(checkros, cloudspaces)
    if not any(results):  # all ok.
        results = [dict(state='OK', category=category, message="All RouterOS are OK.")]
    results = [x for x in results if x]  # remove nones.
    return results

if __name__ == "__main__":
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
