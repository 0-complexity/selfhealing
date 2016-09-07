from JumpScale import j
import re

descr = """
Monitor if a network bond (if there is one) has both (or more) interfaces properly active.
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
    category = "Hardware"
    rc, output = j.system.process.execute('ovs-appctl bond/show', dieOnNonZeroExitCode=False)
    results = []
    if rc == 127:
        return []
    elif rc != 0:
        msg = 'Failed to execute ovs-appctl'
        results.append({'message': msg, 'uid': msg, 'category': category, 'state': 'ERROR'})
    else:
        bonds = []
        bond = {}
        for match in re.finditer('(?:---- bond-(?P<bondname>\w+) ----)?.+?\n(?:slave (?:(?P<slavename>\w+): (?P<state>\w+)))', output, re.DOTALL):
            groups = match.groupdict()
            slave = {'name': groups['slavename'], 'state': groups['state']}
            if groups['bondname']:
                if bond:
                    bonds.append(bond)
                bond = {'name': groups['bondname']}
            bond.setdefault('slaves', []).append(slave)
        if bond:
            bonds.append(bond)

        for bond in bonds:
            badslaves = []
            for slave in bond['slaves']:
                if slave['state'] != 'enabled':
                    badslaves.append(bond['name'])
            state = 'OK'
            if badslaves:
                msg = 'Bond: {} has problems with slaves {}'.format(bond['name'], ', '.join(badslaves))
                state = 'ERROR'
            else:
                msg = 'Bond: {}, all slave are ok'.format(bond['name'])

            result = {'mesage': msg, 'category': category, 'uid': msg + str(j.application.whoAmI), 'state': state}
            results.append(result)
    return results

if __name__ == '__main__':
    import yaml; print(yaml.dump(action(), default_flow_style=False))
