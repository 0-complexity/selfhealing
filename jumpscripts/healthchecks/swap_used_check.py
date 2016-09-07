from JumpScale import j

descr = """
This healthcheck checks if the amount of swap used by the system is higher than expected.

Currently throws WARNING if more than 1GB interrupts  and throws ERROR if more than 2GB interrupts
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
log = True
queue = 'process'


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.memory.swap.used@phys.{}.{}'.format(gid, nid))

    avg_swap_used = stat.h_avg
    level = None
    result = dict()
    result['state'] = 'OK'
    result['message'] = 'Swap used value is: %.2f/s' % avg_swap_used
    result['category'] = 'CPU'
    if avg_swap_used > 2000:
        level = 1
        result['state'] = 'ERROR'
        result['uid'] = 'Swap used value is too large'

    elif avg_swap_used > 1000:
        level = 2
        result['state'] = 'WARNING'
        result['uid'] = 'Swap used value is too large'

    if level:
        msg = 'Swap used is to high current value: %.2f/s' % avg_swap_used
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = nid
        eco.gid = gid
        eco.process()

    return [result]


if __name__ == '__main__':
    print(action())
