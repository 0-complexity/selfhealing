from JumpScale import j

descr = """
Checks whether all configured RAID devices are still healthy.
Result will be shown in the "Hardware" section of the Grid Portal / Status Overview / Node Status page.
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
    import mdstat
    category = "Hardware"
    results = []

    try:
        stats = mdstat.parse()
    except IOError as e:
        if e.errno == 2:
            return []

    for name, device in stats['devices'].iteritems():
        faultydisks = []
        if device['active']:
            for diskname, disk in device['disks'].iteritems():
                if disk['faulty']:
                    faultydisks.append(diskname)
            result = {'state': 'OK', 'category': category}
            if len(faultydisks) != 0:
                msg = 'RAID device {} type {} has problems with disks ({})'.format(name, device['personality'], ', '.join(faultydisks))
                result['uid'] = msg
                result['state'] = 'ERROR'
            else:
                msg = 'RAID device {} OK'.format(name)
            result['message'] = msg
            results.append(result)

    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
