from JumpScale import j

descr = """
Checks the number of CPU context switches per second. If higher than expected an error condition is thrown.

Currently throws:
- WARNING if more than 1M context switches/s
- ERROR if more than 600k context switches/s

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.

TODO : check these values, specifically if amount of cores per CPU is growing
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 15 * 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = True
queue = 'process'
roles = ['node']


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.CPU.contextswitch@phys.{}.{}'.format(gid, nid))

    result = dict()
    result['state'] = 'OK'
    result['category'] = 'System Load'
    result['uid'] = 'CPU context switch'
    
    if stat is None:
        result['state'] = 'WARNING'
        result['message'] = 'CPU context switch is not collected yet'
        return [result]

    avgctx = stat.h_avg
    result['message'] = 'Number of CPU context switches per second: %.2f/s' % avgctx
    if avgctx > 1000000:
        result['state'] = 'ERROR'

    elif avgctx > 600000:
        result['state'] = 'WARNING'

    return [result]


if __name__ == '__main__':
    print(action())
