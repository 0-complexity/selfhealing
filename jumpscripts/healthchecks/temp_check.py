from JumpScale import j

descr = """
Checks the temperature on the system.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60  # 1min
enable = True
async = True
queue = 'process'
log = True

def action():
    category = "Temperature"
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    import multiprocessing
    rcl = j.clients.redis.getByInstance('system')
    labeled = sorted(glob.glob("/sys/class/hwmon/*/temp*_label")
    for coreid in range(multiprocessing.cpu_count()):
        key = "machine.CPU.temperature@phys.{gid}.{nodeid}.{coreid}".format(gid=gid, nid=nid, coreid=coreid)
        statsclient = j.tools.aggregator.getClient(rcl, key)
        stat = statsclient.statGet(key)
        filelabel = stat.tags['filelabel']
        label = open(filelabel).read()
        crit = int(open(filelabel.replace("_label", "_crit")).read())
        maxt = int(open(filelabel.replace("_label", "_max")).read())
        inputtemp = stat.m_avg
        if stat > crit:
            results.append(dict(state='ERROR', category=category, message="Temperature on {label} = {inputtemp} > critical {critical}".format(label=label, inputtemp=inputtemp, critical=crit)))
        elif stat > maxt:
            results.append(dict(state='WARNING', category=category, message="Temperature on {label} = {inputtemp} > max {maxt}".format(label=label, inputtemp=inputtemp, maxt=maxt)))
        else:
            results.append(dict(state='OK', category=category, message="Temperature on {label} = {inputtemp} OK".format(label=label, inputtemp=inputtemp)))

    return results

if __name__ == '__main__':
    print action()
