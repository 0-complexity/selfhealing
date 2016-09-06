from JumpScale.grid.serverbase.Exceptions import RemoteException
from JumpScale import j

descr = """
This healthcheck checks if memory and CPU usage on average over 1hr per CPU is higher than expected.

For both memory and CPU usage throws WARNING if more than 80% used and throws ERROR if more than 95% used

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
    import psutil
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.memory.ram.available@phys.{}.{}'.format(gid, nid))
    totalram = psutil.phymem_usage().total
    avgmempercent = (stat.h_avg / float(totalram)) * 100

    cpupercent = 0
    count = 0
    for percent in statsclient.statsByPerfix('machine.CPU.percent@phys.%d.%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)):
        count += 1
        cpupercent += percent.h_avg
    cpuavg = cpupercent / float(count)

    return get_results('memory', avgmempercent), get_results('cpu', cpuavg)


def get_results(type_, percent):
    res = list()

    level = None
    result = dict()
    result['state'] = 'OK'
    result['message'] = r'%s load -> last hour avergage is: %s %%' % (type_.upper(), percent)
    result['category'] = 'CPU'
    if percent > 95:
        level = 1
        result['state'] = 'ERROR'
        result['uid'] = r'%s load -> last hour avergage is too high' % (type_.upper())
    elif percent > 80:
        level = 2
        result['state'] = 'WARNING'
        result['uid'] = r'%s load -> last hour avergage is too high' % (type_.upper())
    if level:
        #  500_6_cpu.promile
        msg = '%s load -> above treshhold avgvalue last hour avergage is: %s %%' % (type_.upper(), percent)
        result['message'] = msg
        eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
        eco.nid = j.application.whoAmI.nid
        eco.gid = j.application.whoAmI.gid
        eco.process()
    res.append(result)
    return res

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()
