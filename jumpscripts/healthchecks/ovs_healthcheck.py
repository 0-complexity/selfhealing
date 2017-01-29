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
period = "%s,%s * * * *" % (interval, interval + 30)
timeout = 60 * 5
enable = True
async = True
queue = 'process'
log = True

LOG_TYPES = {0: 'ERROR',  # FAILURE
             1: 'OK',  # SUCCESS
             2: 'WARNING',
             3: 'OK',  # info
             4: 'ERROR',  # EXCEPTION
             5: 'SKIPPED',
             6: 'DEBUG'}


def action():
    import sys
    sys.path.insert(0, '/opt/OpenvStorage')
    from ovs.extensions.healthcheck.openvstorage.openvstoragecluster_health_check import OpenvStorageHealthCheck
    from ovs.extensions.healthcheck.arakoon.arakooncluster_health_check import ArakoonHealthCheck
    from ovs.extensions.healthcheck.volumedriver.volumedriver_health_check import VolumedriverHealthCheck
    from ovs.extensions.healthcheck.alba.alba_health_check import AlbaHealthCheck
    from ovs.log.healthcheck_logHandler import HCLogHandler

    module = {'name': ''}

    def failure(self, msg, test_name=None):
        results.append({'message': msg, 'uid': test_name, 'category': module['name'], 'state': 'ERROR'})

    def success(self, msg, test_name=None):
        results.append({'message': msg, 'uid': test_name, 'category': module['name'], 'state': 'OK'})

    def warning(self, msg, test_name=None):
        results.append({'message': msg, 'uid': test_name, 'category': module['name'], 'state': 'WARNING'})

    HCLogHandler.failure = failure
    HCLogHandler.success = success
    HCLogHandler.warning = warning
    logger = HCLogHandler(print_progress=False)
    results = []

    def run(check, name):
        module['name'] = name
        try:
            check.run(logger)
        except Exception as e:
            eco = j.errorconditionhandler.processPythonExceptionObject(e)
            msg = 'Failure in check see [eco|/grid/error condition?id={}]'.format(eco.guid)
            results.append({'message': msg, 'category': name, 'state': 'ERROR'})

    run(OpenvStorageHealthCheck, 'OpenvStorage')
    run(ArakoonHealthCheck, 'Arakoon')
    run(VolumedriverHealthCheck, 'Volumedriver')
    run(AlbaHealthCheck, 'Alba')

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
