from JumpScale import j
import re


descr = """
gather statistics about system
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitoring.processes"
period = 60 #always in sec
timeout = period * 0.2
enable=True
async=True
queue='process'
log=False

roles = []

def action():
    import psutil
    import os
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    results={}
    val=psutil.cpu_percent()
    results["cpu.percent"]=val
    cput= psutil.cpu_times()
    for key in cput.__dict__.keys():
        val=cput.__dict__[key]
        results["cpu.time.%s"%(key)]=val

    counter=psutil.network_io_counters(False)
    bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout=counter
    results["network.kbytes.recv"]=round(bytes_recv/1024.0,0)
    results["network.kbytes.send"]=round(bytes_sent/1024.0,0)
    results["network.packets.recv"]=packets_recv
    results["network.packets.send"]=packets_sent
    results["network.error.in"]=errin
    results["network.error.out"]=errout
    results["network.drop.in"]=dropin
    results["network.drop.out"]=dropout

    avg1min, avg5min, avg15min = os.getloadavg()
    results["load.avg1min"] = avg1min
    results["load.avg5min"] = avg5min
    results["load.avg15min"] = avg15min

    memory=psutil.virtual_memory()
    results["memory.used"]=round((memory.used - memory.cached)/1024.0/1024.0,2)
    results["memory.cached"]=round(memory.cached/1024.0/1024.0,2)
    results["memory.free"]=round(memory.total/1024.0/1024.0,2) - results['memory.used'] - results['memory.cached']
    results["memory.percent"]=memory.percent

    total,used,free,percent,sin,sout=psutil.virtmem_usage()
    results["swap.free"]=round(free/1024.0/1024.0,2)
    results["swap.used"]=round(used/1024.0/1024.0,2)
    results["swap.percent"]=percent


    stat = j.system.fs.fileGetContents('/proc/stat')
    stats = dict()
    for line in stat.splitlines():
        _, key, value = re.split("^(\w+)\s", line)
        stats[key] = value

    num_ctx_switches = int(stats['ctxt'])

    results["cpu.num_ctx_switches"]=num_ctx_switches

    for key, value in results.iteritems():
        key = "%s_%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid, key)
        tags = 'gid:%d nid:%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid)
        aggregatorcl.measure(key, tags, value, timestamp=None)

    return results

if __name__ == '__main__':
    results = action()
    import yaml
    print yaml.dump(results)
