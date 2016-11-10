from JumpScale import j
descr = """
Checks every predefined period (default 60 seconds) if all OVS processes are still run.
Result will be shown in the "OVS Services" section of the Grid Portal / Status Overview / Node Status page.
Shows WARNING if process not running anymore.
"""

organization = 'cloudscalers'
author = "khamisr@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['storagenode']
period = 60 # 1min
enable = True
async = True
queue = 'process'
log = True

def action():
    ovsresults = list()
    ovscmds = {'OK': 'initctl list | grep ovs | grep start/running | sort',
               'HALTED': 'initctl list | grep ovs | grep -v start/running | sort'}
    for service, enabled in j.system.platform.ubuntu.listServices().iteritems():
        if service.startswith('ovs') or service.startswith('alba') or service.startswith('arakoon'):
            if enabled == 'enabled':
                state = 'RUNNING' if j.system.platform.ubuntu.statusService(service) else 'HALTED'
                ovsresults.append({'message': service, 'uid': service, 'category': 'OVS Services', 'state': state})

    return ovsresults


if __name__ == '__main__':
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
