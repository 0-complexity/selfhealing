from JumpScale import j
descr = """
Checks the status of each stack (CPU node).

ERROR state is automatically attributed to a stack by OpenvCloud - this is done if a specific action cannot be executed anymore on the CPU Node.

Result will be shown in the "Stack Status" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "deboeckj@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['cpunode']
period = 60 * 5  # 30min
timeout = 60 * 1
enable = True
async = True
queue = 'process'
log = True


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    ccl = j.clients.osis.getNamespace('cloudbroker')
    stacks = ccl.stack.search({'referenceId': str(nid), 'gid': gid})[1:]
    category = 'Stack Status'
    if not stacks:
        return [{'message': 'Node with role CPUNode is not configured as stack',
                 'uid': category,
                 'category': category,
                 'state': 'ERROR'}
                ]
    stack = stacks[0]
    if stack['status'] == 'ERROR':
        return [{'message': 'Node is in error state',
                 'uid': category,
                 'category': category,
                 'state': 'ERROR'}
                ]
    elif stack['status'] == 'ENABLED':
        return [{'message': 'Node is enabled',
                 'category': category,
                 'state': 'OK',
                 'uid': category}
                ]
    elif stack['status'] in ['MAINTENANCE', 'DECOMISSIONED']:
        return [{'message': 'Node state is %s' % stack['status'],
                 'uid': category,
                 'category': category,
                 'state': 'SKIPPED'}
                ]
    else:
        return [{'message': 'Node has an invalid state %s' % stack['status'],
                 'uid': category,
                 'category': category,
                 'state': 'ERROR'}
                ]

if __name__ == '__main__':
    print action()
