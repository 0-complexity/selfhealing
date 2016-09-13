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
roles = ['cpunode', 'storagenode', 'storagedriver',]


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    ocl = j.clients.osis.getByInstance('main')
    ncl = j.clients.osis.getCategory(ocl, 'system', 'node')
    current_node = ncl.search({'roles': {'$in': roles}, 'id': nid})[1]
    nodes = ncl.search({'roles': {'$in': roles}, 'active': True, 'gid': gid, 'id': {'$ne': nid}})[1:]
    results = []
    category = 'ovs_healthcheck'

    # make sure we actually have ssh key
    if not j.system.fs.exists('/root/.ssh/id_rsa'):
        j.system.platform.ubuntu.generateLocalSSHKeyPair(passphrase='', type='rsa', overwrite=True, path='/root/.ssh/id_rsa')
    if not j.system.fs.exists('/root/.ssh/id_rsa.pub'):
        j.system.process.execute('ssh-keygen -y -f /root/.ssh/id_rsa > /root/.ssh/id_rsa.pub')

    # update public keys in the db
    current_node['publickeys'] = []
    for path in j.system.fs.listFilesInDir('/root/.ssh/', filter='*.pub'):
        public_key = j.system.fs.fileGetContents(path).strip()
        if public_key not in current_node['publickeys']:
            current_node['publickeys'].append(public_key)

    # update the hostkey in the db
    if j.system.fs.exists('/etc/ssh/ssh_host_rsa_key.pub'):
        current_node['hostkey'] = j.system.fs.fileGetContents('/etc/ssh/ssh_host_rsa_key.pub').strip()
    else:
        msg = "node %s doesn't have host key file at /etc/ssh/ssh_host_rsa_key.pub" % current_node['name']
        results.append({'state': 'ERROR', 'category': category, 'message': msg, 'uid': msg})
    # save node to db
    ncl.set(current_node)

    if j.system.fs.exists('/root/.ssh/authorized_keys'):
        authorized_keys = j.system.fs.fileGetContents('/root/.ssh/authorized_keys')
    else:
        authorized_keys = ''
        j.system.fs.writeFile('/root/.ssh/authorized_keys', authorized_keys)

    if j.system.fs.exists('/root/.ssh/known_hosts'):
        known_hosts = j.system.fs.fileGetContents('/root/.ssh/known_hosts')
    else:
        known_hosts = ''
        j.system.fs.writeFile('/root/.ssh/known_hosts', known_hosts)

    known_hosts = known_hosts.splitlines()
    authorized_keys = authorized_keys.splitlines()

    changes = {
        'public': False,
        'host': False
    }
    for node in nodes:
        if len(node['publickeys']) <= 0:
            msg = "node %s doesn't have keys from node %s" % (current_node['name'], node['name'])
            results.append({'state': 'ERROR', 'category': category, 'message': msg, 'uid': msg})
        else:
            for key in node['publickeys']:
                key = key.strip()
                if key not in authorized_keys:
                    authorized_keys.append(key)
                    changes['public'] = True
            msg = "node %s have keys from node %s" % (current_node['name'], node['name'])
            results.append({'state': 'OK', 'category': category, 'message': msg, 'uid': msg})

        if node['hostkey'].strip() == '' and node['hostkey'].strip() not in known_hosts:
            msg = "node %s doesn't have host key from node %s" % (current_node['name'], node['name'])
            results.append({'state': 'ERROR', 'category': category, 'message': msg, 'uid': msg})
        else:
            if node['hostkey'].strip() not in known_hosts:
                known_hosts.append(node['hostkey'].strip())
                changes['host'] = True
            msg = "node %s have host key from node %s" % (current_node['name'], node['name'])
            results.append({'state': 'OK', 'category': category, 'message': msg, 'uid': msg})

    if changes['public'] is True:
        j.system.fs.writeFile('/root/.ssh/authorized_keys', '\n'.join(authorized_keys))
    if changes['host'] is True:
        j.system.fs.writeFile('/root/.ssh/known_hosts', '\n'.join(known_hosts))

    return results

if __name__ == '__main__':
    print(action())
