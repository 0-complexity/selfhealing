from JumpScale import j

descr = """
Check the bandwith consumption of the network
"""
organization = "cloudscalers"
author = "deboeckj@greenitglobe.com"
order = 1
enable = True
async = True
log = True
queue = 'process'
period = 180
roles = ['storagenode', 'storagedriver', 'cpunode']
category = "monitor.healthcheck"


def action():
    tmessage = {'state': 'OK', 'category': 'Network'}
    results = []

    nodekey = j.application.getAgentId()
    rcl = j.clients.redis.getByInstance('system')
    statsclient = j.tools.aggregator.getClient(rcl, nodekey)
    for stat in statsclient.statsByPrefix('network.throughput'):
        nic = stat.tagObject.tagGet('nic')
        direction = stat.key.split('@')[0].split('.')[2]
        message = tmessage.copy()
        try:
            nicspeed = j.system.net.getNicSpeed(nic) / 8.  # nic speed is expressed in mbit but we want mbytes
        except:
            continue

        percent = (stat.m_last / float(nicspeed)) * 100
        message['message'] = 'Nic {} {} bandwith is {:.2f}%'.format(nic, direction, percent)
        if percent > 80:
            results.append(message)
            message['state'] = 'WARNING'
        elif percent > 90:
            results.append(message)
            message['state'] = 'ERROR'
    if not results:
        results.append({'state': 'OK', 'category': 'Network', 'message': 'All network bandwith is within boundries'})
    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
