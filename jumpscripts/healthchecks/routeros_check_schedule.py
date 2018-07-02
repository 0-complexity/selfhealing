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
period = 15 * 60  # 15mins.
roles = ['controller']
queue = 'process'
timeout = 180 # 3mins


def action():
    acl = j.clients.agentcontroller.get()
    results = []

    job = acl.executeJumpscript('greenitglobe', 'routeros_check', role='cpunode', gid=j.application.whoAmI.gid)
    if job['state'] == 'OK':
        results.extend(job['result'])
    if not results:
        results.append({'state': 'OK', 'category': 'Network', 'message': 'All RouterOS devices are OK.'})
    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
