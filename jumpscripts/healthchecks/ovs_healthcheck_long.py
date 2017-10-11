from JumpScale import j
descr = """
Calls the standard Open vStorage health checks, see: https://github.com/openvstorage/openvstorage-health-check
Result will be shown in the "OpenvStorage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "foudaa@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['storagedriver']
interval = (2 * j.application.whoAmI.nid) % 30
period = "%s,%s 4 * * *" % (interval, interval + 30)
timeout = 60 * 5
enable = True
async = True
queue = 'process'
log = True


def action():
    from CloudscalerLibcloud import openvstorage
    results = []

    longtests = (
        ('alba', 'Alba', ['disk-safety-test']),
        ('ovs', 'OpenvStorage', ['dns-test', 'model-test', 'packages-test', 'directories-test', 'log-files-test', 'zombie-processes-test'],),
        ('arakoon', 'Arakoon', ['collapse-test', 'consistency-test']),
    )

    for modulename, category, tests in longtests:
        for test in tests:
            results.extend(openvstorage.run_healthcheck(modulename, test, category))

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
