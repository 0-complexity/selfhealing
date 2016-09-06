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
period = 15*60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = True
queue ='process'

def action():
    osiscl = j.clients.osis.getNamespace('system')
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    try:
        cpuresults = osiscl.stats.search('select mean(value) from "%s_%s_cpu.percent.gauge" where time > now() - 1h group by time(1h)' %
            (gid, nid))
        memresults = osiscl.stats.search('select mean(value) from "%s_%s_memory.percent.gauge" where time > now() - 1h group by time(1h)' %
            (gid, nid))
    except RemoteException , e:
        return [{'category':'CPU', 'state':'ERROR', 'message':'influxdb is halted cannot access data', 'uid':'influxdb is halted cannot access data'}]

    try:
        return get_results(cpuresults['series']) + get_results(memresults['series'])
    except (KeyError,IndexError):
        return [{'category':'CPU', 'state':'WARNING', 'message':'Not enough data collected', 'uid':'Not enough data collected'}]


def get_results(series):
    res = list()
    for sira in series:

        parts = sira['name'].split('.')[0]
        type = parts.split('_')[2]
        avgvalue = sira['values'][1][1]
        level = None
        result = dict()
        result ['state'] = 'OK'
        result ['message'] =  r'%s load -> last hour avergage is: %s %%' %(type.upper(), avgvalue)
        result ['category'] = 'CPU'
        if avgvalue > 95:
            level = 1
            result['state'] = 'ERROR'
            result ['uid'] =  r'%s load -> last hour avergage is too high' %(type.upper())
        elif avgvalue > 80:
            level = 2
            result['state'] = 'WARNING'
            result ['uid'] =  r'%s load -> last hour avergage is too high' %(type.upper())
        if level:
            #500_6_cpu.promile
            msg = '%s load -> above treshhold avgvalue last hour avergage is: %s %%' % (type.upper(), avgvalue)
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
