from JumpScale import j

descr = """
This script checks if all the nodes have the sshkey from the other nodes authorized.
"""

organization = "jumpscale"
author = "deboeckj@greenitglobe.com"
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
roles = ['reflector']


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
    nid = j.application.whoAmI.nid
    ncl = j.clients.osis.getNamespace('system').node
    current_node = ncl.get(nid).dump()
    roles = ['cpunode', 'storagenode', 'storagedriver', ]

    nodes = ncl.search({'roles': {'$in': roles}, 'active': True})[1:]

    # update the hostkey in the db
    if j.system.fs.exists('/etc/ssh/ssh_host_rsa_key.pub'):
        key = j.system.fs.fileGetContents('/etc/ssh/ssh_host_rsa_key.pub')
        key2 = key.split(' ')[:-1]
        current_node['hostkey'] = ' '.join(key2)
    else:
        print "node %s doesn't have host key file at /etc/ssh/ssh_host_rsa_key.pub" % current_node['name']
    # save node to db
    ncl.set(current_node)

    if j.system.fs.exists('/home/guest/.ssh/authorized_keys'):
        authorized_keys = j.system.fs.fileGetContents('/home/guest/.ssh/authorized_keys')
    else:
        authorized_keys = ''
        j.system.fs.writeFile('/home/guest/.ssh/authorized_keys', authorized_keys)

    authorized_keys = cleanup_list(authorized_keys.splitlines())
    authlen = len(authorized_keys)

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

    if changes['public'] is True or authlen != len(authorized_keys):
        print 'Writing authorized_keys'
        authorized_keys.append('')
        j.system.fs.writeFile('/home/guest/.ssh/authorized_keys', '\n'.join(authorized_keys))

if __name__ == '__main__':
    action()
