from JumpScale import j

descr = """
This healthcheck checks if amount of interrupts is higher than expected.

Currently throws WARNING if more than 8K interrupts and throws ERROR if more than 10K interrupts
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


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.CPU.interrupts@phys.{}.{}'.format(gid, nid))

    result = dict()
    result['state'] = 'OK'
    result['category'] = 'System Load'

    if stat is None:
        result['state'] = 'WARNING'
        result['message'] = 'Number of interrupts is not collected yet'
        result['uid'] = result['message']
        return [result]

    avg_inter = stat.h_avg
    result['message'] = 'Number of interrupts value is: %.2f/s' % avg_inter
    level = None
    if avg_inter > 10000:
        level = 1
        result['state'] = 'ERROR'
        result['uid'] = 'Number of interrupts value is too large'

    elif avg_inter > 80000:
        level = 2
        result['state'] = 'WARNING'
        result['uid'] = 'Number of interrupts value is too large'

    if level:
        msg = 'Number of interrupts is to high current value: %.2f/s' % avg_inter
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = nid
        eco.gid = gid
        eco.process()

    return [result]


if __name__ == '__main__':
    print(action())
