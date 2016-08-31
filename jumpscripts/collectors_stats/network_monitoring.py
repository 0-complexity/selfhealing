from JumpScale import j
import psutil

descr = """
gather network statistics
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
category = "info.gather.nic"
period = 60 #always in sec
timeout = period * 0.2
enable=True
async=True
queue='process'
roles = []
log=False

def action():
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    counters = psutil.network_io_counters(True)
    pattern = None
    if j.application.config.exists('gridmonitoring.nic.pattern'):
        pattern = j.application.config.getStr('gridmonitoring.nic.pattern')

    for nic, stat in counters.iteritems():
        if pattern and j.codetools.regex.match(pattern,nic) == False:
            continue
        if j.system.net.getNicType(nic) == 'VIRTUAL' and not 'pub' in nic:
            continue
        result = dict()
        bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout = stat
        result['kbytes_sent'] = int(round(bytes_sent/1024.0,0))
        result['kbytes_recv'] = int(round(bytes_recv/1024.0,0))
        result['packets_sent'] = packets_sent
        result['packets_recv'] = packets_recv
        result['errin'] = errin
        result['errout'] = errout
        result['dropin'] = dropin
        result['dropout'] = dropout
        for key, value in result.iteritems():
            key = "%s_%s_nic_%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid, nic, key)
            tags = 'gid:%d nid:%d nic:%s' % (j.application.whoAmI.gid, j.application.whoAmI.nid, nic)
            aggregatorcl.measure(key, tags, value, timestamp=None)

if __name__ == '__main__':
    action()
