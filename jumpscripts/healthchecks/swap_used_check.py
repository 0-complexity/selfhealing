from JumpScale import j

descr = """
Checks the amount of swap used by the system, and throws an error if higher than expected.

Currently throws:
- WARNING if more than 10 GB
- ERROR if more than 14 GB

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 15 * 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
roles = ['node']
log = True
queue = 'process'


def action():
    import psutil
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.memory.swap.used@phys.{}.{}'.format(gid, nid))
    memstat = statsclient.statGet('machine.memory.ram.available@phys.{}.{}'.format(gid, nid))
    totalmemory = psutil.virtual_memory().total / (1024 ** 2)

    result = dict()
    result['state'] = 'OK'
    result['category'] = 'System Load'

    if stat is None or memstat is None:
        level = 2
        result['state'] = 'WARNING'
        result['message'] = 'Swap used value is not available'
        result['uid'] = result['message']
        return [result]

    avg_swap_used = stat.h_avg
    result['message'] = 'Swap used value is: %.2fMB' % avg_swap_used
    level = None

    if memstat.h_avg / totalmemory > 0.8:
        if avg_swap_used > 14000:
            level = 1
            result['state'] = 'ERROR'
            result['uid'] = 'Swap used value is too large'

        elif avg_swap_used > 10000:
            level = 2
            result['state'] = 'WARNING'
            result['uid'] = 'Swap used value is too large'

    if level:
        msg = 'Swap used is too high: %.2fMB' % avg_swap_used
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = nid
        eco.gid = gid
        eco.process()

    return [result]


if __name__ == '__main__':
    print(action())
