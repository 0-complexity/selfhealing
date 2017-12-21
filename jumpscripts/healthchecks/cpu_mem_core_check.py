from JumpScale import j

descr = """
Checks average memory and CPU usage/load. If average per hour is higher than expected an error condition is thrown.

For both memory and CPU usage throws WARNING if more than 80% used and throws ERROR if more than 95% used.

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.
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
    import psutil
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    nodekey = '{}_{}'.format(gid, nid)
    category = 'System Load'

    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    stat = statsclient.statGet('machine.memory.ram.available@phys.{}.{}'.format(gid, nid))
    if stat is None:
        memoryresult = {}
        memoryresult['state'] = 'WARNING'
        memoryresult['category'] = category
        memoryresult['message'] = 'Average memory load is not collected yet'
    else:
        totalram = psutil.phymem_usage().total
        avgmempercent = ((totalram - stat.h_avg) / float(totalram)) * 100
        memoryresult = get_results('memory', avgmempercent)

    cpupercent = 0
    count = 0
    for percent in statsclient.statsByPrefix('machine.CPU.percent@phys.%d.%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)):
        count += 1
        cpupercent += percent.h_avg

    if count == 0:
        cpuresult = {}
        cpuresult['state'] = 'WARNING'
        cpuresult['category'] = category
        cpuresult['message'] = 'Average CPU load is not collected yet'
        cpuresult['uid'] = cpuresult['message']
    else:
        cpuavg = cpupercent / float(count)
        cpuresult = get_results('cpu', cpuavg)

    memoryresult['uid'] = "Memory Load"
    cpuresult['uid'] = "CPU Load"
    return [memoryresult, cpuresult]


def get_results(type_, percent):
    result = dict()
    result['state'] = 'OK'
    result['message'] = r'Average %s load during last hour was: %.2f%%' % (type_.upper(), percent)
    result['category'] = 'System Load'
    if percent > 95:
        result['state'] = 'ERROR'
        result['uid'] = r'Average %s load during last hour was too high' % (type_.upper())
    elif percent > 80:
        result['state'] = 'WARNING'
        result['uid'] = r'Avergage %s load during last hour was too high' % (type_.upper())
    return result


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
