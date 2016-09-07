from JumpScale import j

descr = """
Checks the temperature on the system.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60*5  # 5mins
enable = True
async = True
queue = 'process'
log = True


def action():
    results = []
    category = "Temperature"
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, "{gid}_{nid}".format(gid=gid, nid=nid))

    labeled = sorted(glob.glob("/sys/class/hwmon/*/temp*_label")


    for stat in statsclient.statsByPrefix('machine.CPU.temperature@phys.{gid}.{nid}'.format(gid=gid,nid=nid)):
        filelabel = stat.tags['filelabel']
        label = open(filelabel).read()
        crit = int(open(filelabel.replace("_label", "_crit")).read())
        maxt = int(open(filelabel.replace("_label", "_max")).read())
        inputtemp = stat.m_avg

        if inputtemp > crit:
            results.append(dict(state='ERROR', category=category, message="Temperature on {label} = {inputtemp} > critical {critical}".format(label=label, inputtemp=inputtemp, critical=crit)))
        elif inputtemp > maxt:
            results.append(dict(state='WARNING', category=category, message="Temperature on {label} = {inputtemp} > max {maxt}".format(label=label, inputtemp=inputtemp, maxt=maxt)))

    if len(results) == 0:
        results.append(dict(state='OK', category=category, message="CPU Temperature OK")


    return results

if __name__ == '__main__':
    print action()
