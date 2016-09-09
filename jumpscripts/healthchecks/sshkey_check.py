from JumpScale import j

descr = """
This healthcheck checks if all the storage node can ssh to each others.

It throws error when a node is unreachable from another node.
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = True
queue = 'process'
roles = ['storagedriver',]


def action():
    nid = j.application.whoAmI.nid
    ocl = j.clients.osis.getByInstance('main')
    ncl = j.clients.osis.getCategory(ocl, 'system', 'node')
    current_node = ncl.search({'roles': {'$in': ['storagedriver']}, 'id': nid})[1]
    nodes = ncl.search({'roles': {'$in': ['storagedriver']}, 'id':{'$ne': nid}})[1:]
    results = []

    result = dict()
    result['state'] = 'OK'
    result['category'] = 'ovs_healthcheck'

    for node in nodes:
        for ip in node['ipaddr']:
            con = j.remote.cuisine.connect(addr=ip, port=22, login='root')
            try:
                print 'test connection to %s' % ip
                con.run('ls /')
                msg = 'node %s can reach node %s (%s)' % (current_node['name'], node['name'], ip)
                results.append({'state': 'OK', 'category': category, 'message': msg, 'uid': msg})
            except:
                msg = 'node %s can reach node %s (%s)' % (current_node['name'], node['name'], ip)
                results.append({'state': 'ERROR', 'category': category, 'message': msg, 'uid': msg})

    return results

if __name__ == '__main__':
    print(action())
