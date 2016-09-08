from JumpScale import j

descr = """
Make sure all configured raid devices are still healthy
"""

organization = 'cloudscalers'
author = "deboeckj@greenitglobe.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60  # 1min
enable = True
async = True
queue = 'process'
log = True


def action():
    try:
        import mdstat
    except ImportError:
        j.system.process.execute('pip install mdstat')
        import mdstat
    category = "Hardware"
    results = []

    stats = mdstat.parse()
    for name, device in stats['devices'].iteritems():
        faultydisks = []
        if device['active']:
            for diskname, disk in device['disks'].iteritems():
                if disk['faulty']:
                    faultydisks.append(diskname)
            result = {'state': 'OK', 'category': category}
            if len(faultydisks) != 0:
                msg = 'Raid device {} type {} has problems with disks ({})'.format(name, device['personality'], ', '.join(faultydisks))
                result['uid'] = msg
                result['state'] = 'ERROR'
            else:
                msg = 'Raid device {} OK'.format(name)
            result['message'] = msg
            results.append(result)

    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
