from JumpScale import j
import psutil

descr = """
Gathers following network statistics from the physical machines:
- network.throughput.outgoing
- network.throughput.incoming
- network.packets.tx
- network.packets.rx
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
category = "info.gather.nic"
period = 60  # always in sec
timeout = period * 0.2
enable = True
async = True
queue = 'process'
roles = ['stats']
log = False


def action():
    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    counters = psutil.network_io_counters(True)
    now = j.base.time.getTimeEpoch()
    pattern = None
    if j.application.config.exists('gridmonitoring.nic.pattern'):
        pattern = j.application.config.getStr('gridmonitoring.nic.pattern')

    all_results = {}
    for nic, stat in counters.iteritems():
        if pattern and j.codetools.regex.match(pattern, nic) is False:
            continue

        if j.system.net.getNicType(nic) == 'VIRTUAL' and 'pub' not in nic:
            continue

        result = dict()
        bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout = stat
        result['network.throughput.outgoing'] = int(round(bytes_sent / (1024.0 * 1024), 0))
        result['network.throughput.incoming'] = int(round(bytes_recv / (1024.0 * 1024), 0))
        result['network.packets.tx'] = packets_sent
        result['network.packets.rx'] = packets_recv

        for key, value in result.iteritems():
            key = "%s@phys.%d.%d.%s" % (key, j.application.whoAmI.gid, j.application.whoAmI.nid, nic)
            tags = 'gid:%d nid:%d nic:%s type:physical' % (j.application.whoAmI.gid, j.application.whoAmI.nid, nic)
            aggregatorcl.measureDiff(key, tags, value, timestamp=now)

        all_results[nic] = result

    return all_results


if __name__ == '__main__':
    results = action()
    import yaml
    print(yaml.dump(results))
