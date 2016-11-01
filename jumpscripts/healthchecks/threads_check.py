from JumpScale import j

descr = """
Checks the number of threads, and throw an error if higher than expected.

Currently throws
- WARNING if more than 18K threads
- ERROR if more than 20K threads

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
log = True
queue = 'process'
roles = ['node']


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.process.threads@phys.{}.{}'.format(gid, nid))

    result = dict()
    result['state'] = 'OK'
    result['category'] = 'System Load'

    if stat is None:
        level = 2
        result['state'] = 'WARNING'
        result['message'] = 'Number of threads is not available'
        result['uid'] = result['message']
        return [result]

    avg_thread = int(stat.h_avg)
    result['message'] = 'Number of threads is: %d' % avg_thread
    level = None

    if avg_thread > 20000:
        level = 1
        result['state'] = 'ERROR'
        result['uid'] = 'Number of threads is too high'

    elif avg_thread > 18000:
        level = 2
        result['state'] = 'WARNING'
        result['uid'] = 'Number of threads is too high'

    if level:
        msg = 'Number of threads is too high: %d' % avg_thread
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = nid
        eco.gid = gid
        eco.process()

    return [result]


if __name__ == '__main__':
    print(action())
