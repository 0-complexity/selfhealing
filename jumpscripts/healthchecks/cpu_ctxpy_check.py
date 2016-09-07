from JumpScale import j

descr = """
This healthcheck checks if amount of context switches per CPU is higher than expected.

Currently throws WARNING if more than 1M context switches and throws ERROR if more than 600k context switches

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


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.CPU.contextswitch@phys.{}.{}'.format(gid, nid))

    result = dict()
    result['state'] = 'OK'
    result['category'] = 'CPU'

    if stat is None:
        result['state'] = 'WARNING'
        result['message'] = 'CPU contextswitch is not collected yet'
        result['uid'] = result['message']
        return [result]

    avgctx = stat.h_avg
    result['message'] = 'CPU contextswitch value is: %.2f/s' % avgctx
    level = None
    if avgctx > 1000000:
        level = 1
        result['state'] = 'ERROR'
        result['uid'] = 'CPU contextswitch value is too large'

    elif avgctx > 600000:
        level = 2
        result['state'] = 'WARNING'
        result['uid'] = 'CPU contextswitch value is too large'

    if level:
        msg = 'CPU contextswitch is to high current value: %.2f/s' % avgctx
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = nid
        eco.gid = gid
        eco.process()

    return [result]


if __name__ == '__main__':
    print(action())
