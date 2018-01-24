from JumpScale import j

descr = """
Checks Redis server status.
Result will be shown in the "Redis" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
name = 'info_gather_redis'
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"
async = True
roles = ['node']
queue = 'process'
period = 600
log = True
timeout = 60


def action():
    import JumpScale.baselib.redis
    ports = {}
    results = list()

    for instance in j.atyourservice.findServices(name='redis'):

        if not instance.isInstalled():
            continue

        for redisport in instance.getTCPPorts():
            if redisport:
                ports[instance.instance] = ports.get(instance.instance, [])
                ports[instance.instance].append(int(redisport))

    for instance, ports_val in ports.iteritems():
        for port in ports_val:
            result = {'category': 'Redis', 'uid': "redis:{}:port:{}".format(instance, port), 'state': 'OK'}
            results.append(result)
            errmsg = 'Redis is not operational (halted or not installed)'
            try:
                rcl = j.clients.redis.getByInstance(instance)
                if rcl.ping():
                    state = 'OK'
                else:
                    result['state'] = 'ERROR'
                    result['message'] = 'Failed to ping redis.'
                    continue
            except ConnectionError:
                result['state'] = 'ERROR'
                result['message'] = errmsg
                continue

            maxmemory = float(rcl.config_get('maxmemory').get('maxmemory', 0))
            used_memory = rcl.info()['used_memory']
            size, unit = j.tools.units.bytes.converToBestUnit(used_memory)
            msize, munit = j.tools.units.bytes.converToBestUnit(maxmemory)
            used_memorymsg = '%.2f %sB' % (size, unit)
            maxmemorymsg = '%.2f %sB' % (msize, munit)
            result['message'] = '*Port*: %s. *Memory usage*: %s/ %s' % (port, used_memorymsg, maxmemorymsg)

            if (used_memory / maxmemory) * 100 > 90:
                state = 'WARNING'

            result['state'] = state
            print results

    return results

if __name__ == "__main__":
    print action()
