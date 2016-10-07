from JumpScale import j

descr = """
Scheduler that runs on master to check for dead RouterOS devices.

"""

organization = 'cloudscalers'
category = "monitor.healthcheck"
author = "thabeta@codescalers.com"
version = "1.0"

enable = True
async = True
period = 15*60  # 15mins.
roles = ['master']
queue = 'process'


def action():
    acl = j.clients.agentcontroller.get()
    ccl = j.clients.osis.getNamespace('cloudbroker')
    results = []

    for location in ccl.location.search({})[1:]:
        job = acl.executeJumpscript('greenitglobe', 'routeros_check', role='cpunode', gid=location['gid'])
        if job['state'] == 'OK':
            results.extend(job['result'])
    if not results:
        results.append({'state': 'OK', 'category': 'Network', 'message': 'All RouterOS devices are OK.'})
    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
