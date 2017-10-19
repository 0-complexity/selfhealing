from JumpScale import j

descr = """
Checks the CPU + disk temperature of the system.
Result will be shown in the "Temperature" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60 * 5  # 5mins
enable = True
async = True
queue = 'process'
log = True


def action():
    results = []
    cputempresults = []
    disktempresults = []
    category = "Temperature"
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    disk_uid = "Disk Temp"
    cpu_uid = "CPU Temp"
    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, "{gid}_{nid}".format(gid=gid, nid=nid))
    for stat in statsclient.statsByPrefix('machine.CPU.temperature@phys.{gid}.{nid}'.format(gid=gid, nid=nid)):
        filelabel = stat.tagObject.tags['labelfile']
        label = open(filelabel).read()
        crit = int(open(filelabel.replace("_label", "_crit")).read())
        maxt = int(open(filelabel.replace("_label", "_max")).read())
        inputtemp = stat.m_avg

        if inputtemp > crit:
            cputempresults.append(dict(state='ERROR', category=category, uid=cpu_uid, message="Temperature on {label} = {inputtemp} > critical {critical}".format(label=label, inputtemp=inputtemp, critical=crit)))
        elif inputtemp > maxt:
            cputempresults.append(dict(state='WARNING', category=category, uid=cpu_uid, message="Temperature on {label} = {inputtemp} > max {maxt}".format(label=label, inputtemp=inputtemp, maxt=maxt)))

    for stat in statsclient.statsByPrefix('machine.disk.temperature@phys.{gid}.{nid}'.format(gid=gid, nid=nid)):
        key = stat.key
        diskid = key.split(".")[-1]
        disktemp = stat.m_avg
        wtemp = 60
        etemp = 70

        if disktemp > etemp:
            disktempresults.append(dict(state='ERROR', category=category, uid=disk_uid, message="Temperature on disk {disk} = {disktemp}".format(disk=diskid, disktemp=disktemp)))
        elif disktemp > wtemp:
            disktempresults.append(dict(state='WARNING', category=category, uid=disk_uid, message="Temperature on disk {disk} = {disktemp}".format(disk=diskid, disktemp=disktemp)))

    if len(cputempresults) == 0:
        cputempresults.append(dict(state='OK', category=category, uid=cpu_uid, message="CPU temperature is OK."))
    if len(disktempresults) == 0:
        disktempresults.append(dict(state='OK', category=category, uid=disk_uid, message="Disks temperature is OK."))

    results = cputempresults + disktempresults
    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
