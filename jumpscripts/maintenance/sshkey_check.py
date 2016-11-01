from JumpScale import j

descr = """
This script checks if all the nodes have the sshkey from the other nodes authorized.
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['cpunode', 'storagenode', 'storagedriver', ]


def cleanup_list(l):
    """
    remove emtpy elememt from list, dedupe items and strip;
    """
    s = set(l)
    if '' in s:
        s.remove('')
    l = list(s)
    for i, val in enumerate(l):
        l[i] = l[i].strip()
    return l


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    ncl = j.clients.osis.getNamespace('system').node
    current_node = ncl.get(nid).dump()
    nodes = ncl.search({'roles': {'$in': roles}, 'active': True, 'gid': gid, 'id': {'$ne': nid}})[1:]
    nodes += ncl.search({'roles': {'$in': ['reflector']}, 'active': True})[1:]

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
        key = j.system.fs.fileGetContents('/etc/ssh/ssh_host_rsa_key.pub')
        key2 = key.split(' ')[:-1]
        current_node['hostkey'] = ' '.join(key2)
    else:
        print "node %s doesn't have host key file at /etc/ssh/ssh_host_rsa_key.pub" % current_node['name']
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

    known_hosts = cleanup_list(known_hosts.splitlines())
    authorized_keys = cleanup_list(authorized_keys.splitlines())

    changes = {
        'public': False,
        'host': False
    }
    for node in nodes:
        # deal with public keys
        if len(node['publickeys']) <= 0:
            print "node %s doesn't have keys from node %s" % (current_node['name'], node['name'])
        else:
            for key in node['publickeys']:
                key = key.strip()
                if key not in authorized_keys:
                    authorized_keys.append(key)
                    changes['public'] = True

            print "node %s have keys from node %s" % (current_node['name'], node['name'])

        # deal with host keys
        hostkey = node['hostkey'].strip()
        if hostkey == '' and hostkey not in known_hosts:
            print "node %s doesn't have host key from node %s" % (current_node['name'], node['name'])
        else:
            nodeips = []
            for net in node['netaddr']:
                if net['name'] in ['lo', 'gw_mgmt', 'vxbackend']:
                    continue
                for ip in net['ip']:
                    nodeips.append(ip)
            entry = '{} {}'.format(','.join(sorted(nodeips)), node['hostkey'])
            if entry not in known_hosts:
                known_hosts.append(entry)
                changes['host'] = True

                print "node %s have host key from node %s" % (current_node['name'], node['name'])

    if changes['public'] is True:
        print 'Writing authorized_keys'
        authorized_keys.append('')
        j.system.fs.writeFile('/root/.ssh/authorized_keys', '\n'.join(authorized_keys))
    if changes['host'] is True:
        print 'Writing known_hosts'
        known_hosts.append('')
        j.system.fs.writeFile('/root/.ssh/known_hosts', '\n'.join(known_hosts))

if __name__ == '__main__':
    action()
