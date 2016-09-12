from JumpScale import j
import time
import json
from ovs.dal.hybrids.albabackend import AlbaBackend
from ovs.dal.lists.albabackendlist import AlbaBackendList

descr = """
gather statistics about OVS backends
"""

organization = "jumpscale"
author = "christophe@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "disk.monitoring"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
queue = 'process'
log = False

roles = ['storagerouter']


def format_tags(tags):
    out = ''
    for k, v in tags.iteritems():
        out += "%s:%s " % (k, v)
    return out.strip()


def amIMaster():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    ocl = j.clients.osis.getByInstance('main')
    nodecl = j.clients.osis.getCategory(ocl, 'system', 'node')

    nodes = nodecl.search({'roles': 'storagedriver'})[1:]
    nodes = sorted(nodes, key=lambda k: k['id'])

    if nodes[0]['gid'] != gid or nodes[0]['id'] != nid:
        return False

    return True


def action():
    """
    Send OVS backend statistics to DB
    """
    if not amIMaster():
        return {}

    rediscl = j.clients.redis.getByInstance('system')
    aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid))

    all_results = {}

    abl = AlbaBackendList.get_albabackends()
    for ab in abl:
        try:
            gets = 0
            puts = 0
            for guid in ab.linked_backend_guids:
                alba_backend = AlbaBackend(guid)
                gets += alba_backend.statistics['multi_get']['n']
                puts += alba_backend.statistics['apply']['n']
            local_summary = ab.local_summary
            size = local_summary['sizes']
            devices = local_summary['devices']

            now = j.base.time.getTimeEpoch()

            tags = {
                'backend_name': ab.name
                'gid': j.application.whoAmI.gid,
                'nid': j.application.whoAmI.nid,
            }
            result = {
                'gets': gets,
                'puts': puts,
                'free': float(size['size'] - size['used']),
                'used': float(size['used']),
                'green': int(devices['green']),
                'orange': int(devices['orange']),
                'red': int(devices['red'])
            }
            for key, value in result.iteritems():
                key = "ovs.backend.%s@%s" % (key, ab.name)
                aggregatorcl.measure(key, format_tags(tags), value, timestamp=now)

            all_results[ab.name] = result

    return all_results

if __name__ == '__main__':
    result = action()
    import yaml
    print yaml.dump(result)
