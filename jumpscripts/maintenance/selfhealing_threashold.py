from JumpScale import j

descr = """
Find all logs known logs files and executes logs truncate
"""

organization = "0-complexity"
author = "muhamada@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitor.maintenance"

async = True
queue = 'process'
roles = ['statscollector']
enable = True
period = 300
log = True

###############
# jumpscale 8 #
###############

IOPS_THRESHOLD = 200
IOPS_REDIS_KEY = 'throttle.iops.%s'

NETS_THRESHOLD = 1  # MB/sec
NETS_PACKET_THRRSHOLD = 500
NETS_REDIS_KEY = 'throttle.net.%s'


def _aggregate(series, tag):
    bytag = {}

    for points in series:
        tag_value = points['tags'][tag]
        if tag_value == '':
            continue
        bytag.setdefault(tag_value, 0)
        value = points['values'][-1][-1]
        bytag[tag_value] += value

    return bytag


def _process_iops(ovc, influx):
    result = influx.query('''SELECT mean(value) FROM /disk.iops.*\|m/ WHERE "type" = 'virtual' AND time > now() - 10m GROUP BY "vdiskid"''')
    if 'series' not in result.raw:
        print('IOPS no data')
        return
    aggregated = _aggregate(result.raw['series'], 'vdiskid')

    for vdiskid, iops in aggregated.items():
        key = IOPS_REDIS_KEY % vdiskid
        if iops > IOPS_THRESHOLD:
            # last 2 values are over IOPS_THRESHOLD. We need to take action.
            # limit IO.
            ovc.api.cloudbroker.qos.limitIO(diskId=int(vdiskid), iops=IOPS_THRESHOLD)
            j.core.db.set(key, 'x')
            continue

        # Unthrottle
        if j.core.db.get(key) is not None:
            ovc.api.cloudbroker.qos.limitIO(diskId=int(vdiskid), iops=0)
            j.core.db.delete(key)


def _process_network(ovc, influx):
    throughput = influx.query('''SELECT mean(value) FROM /network.throughput.*\|m/ WHERE "type" = 'virtual' AND time > now() - 10m GROUP BY "mac"''')
    agg_throughput = _aggregate(throughput.raw['series'], 'mac')

    packet = influx.query('''SELECT value FROM /network.packets.*\|m/ WHERE "type" = 'virtual'  AND time > now() - 10m GROUP BY "mac"''')
    agg_packet = _aggregate(packet.raw['series'], 'mac')

    for mac, count in agg_throughput.items():
        pac = agg_packet.get(mac, 0)

        key = NETS_REDIS_KEY % mac
        if count > NETS_THRESHOLD and pac > NETS_PACKET_THRRSHOLD:
            ovc.api.cloudbroker.qos.limitInternalBandwith(machineMAC=mac, rate=NETS_THRESHOLD, burst=0)
            j.core.db.set(key, 'x')
            continue

        # Unthrottle
        if j.core.db.get(key) is not None:
            ovc.api.cloudbroker.qos.limitInternalBandwith(machineMAC=mac, rate=NETS_THRESHOLD, burst=0)
            j.core.db.delete(key)


def action():
    cfg = j.data.hrd.get(j.sal.fs.joinPaths(j.dirs.hrd, 'ovc.hrd')).getHRDAsDict()
    ovc = j.clients.openvcloud.get(**cfg)

    gw = j.sal.nettools.getDefaultRouter()
    influx = j.clients.influxdb.get(host=gw)

    influx.switch_database('statistics')

    _process_iops(ovc, influx)
    _process_network(ovc, influx)

if __name__ == '__main__':
    action()
