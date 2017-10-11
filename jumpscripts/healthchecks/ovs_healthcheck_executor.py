from JumpScale import j
descr = """
Calls the standard Open vStorage health checks, see: https://github.com/openvstorage/openvstorage-health-check
Result will be shown in the "OpenvStorage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "foudaa@codescalers.com"
version = "1.0"
roles = ['node']
timeout = 60 * 5
enable = True
async = True
queue = 'process'
log = False


def action(longtests):
    from CloudscalerLibcloud import openvstorage
    results = []

    for modulename, category, tests in longtests:
        for test in tests:
            results.extend(openvstorage.run_healthcheck(modulename, test, category))

    return results