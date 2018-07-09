from JumpScale import j
descr = """
Checks the status of each node.

ERROR state is automatically attributed to a node by OpenvCloud - this is done if a specific action cannot be executed anymore on the Node.

Result will be shown in the "Node Status" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "deboeckj@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['cpunode', 'storagenode']
period = 60 * 5  # 30min
timeout = 60 * 1
enable = True
async = True
queue = 'process'
log = True


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    scl = j.clients.osis.getNamespace('system')
    nodes = scl.node.search({'id': nid, 'gid': gid})[1:]
    category = 'Node Status'
    node = nodes[0]
    if node['status'] == 'ERROR':
        return [{'message': 'Node is in error state',
                 'uid': category,
                 'category': category,
                 'state': 'ERROR'}
                ]
    elif node['status'] == 'ENABLED':
        return [{'message': 'Node is enabled',
                 'category': category,
                 'state': 'OK',
                 'uid': category}
                ]
    elif node['status'] in ['MAINTENANCE', 'DECOMISSIONED']:
        return [{'message': 'Node state is %s' % node['status'],
                 'uid': category,
                 'category': category,
                 'state': 'SKIPPED'}
                ]
    else:
        return [{'message': 'Node has an invalid state %s' % node['status'],
                 'uid': category,
                 'category': category,
                 'state': 'ERROR'}
                ]

if __name__ == '__main__':
    print action()
