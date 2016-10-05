from JumpScale import j

descr = """
Checks the number of interrupts per second. If higher than expected an error condition is thrown.

Currently throws:
- WARNING if more than 8K interrupts/s
- ERROR if more than 10K interrupts/s

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.
"""

roles = ['node']
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
        result['message'] = 'Number of interrupts per second is not collected yet'
        result['uid'] = result['message']
        return [result]

    avg_inter = int(stat.h_avg)
    result['message'] = 'Number of interrupts per second is: %d/s' % avg_inter
    level = None
    if avg_inter > 198000:
        level = 1
        result['state'] = 'ERROR'
        result['uid'] = 'Number of interrupts per second is too high'

    elif avg_inter > 180000:
        level = 2
        result['state'] = 'WARNING'
        result['uid'] = 'Number of interrupts per second is too high'

    if level:
        msg = 'Number of interrupts per second is too high: %d/s' % avg_inter
        result['message'] = msg
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = nid
        eco.gid = gid
        eco.process()

    return [result]


if __name__ == '__main__':
    print(action())
