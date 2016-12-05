descr = """
Calls the standard Open vStorage health checks, see: https://github.com/openvstorage/openvstorage-health-check
Result will be shown in the "OpenvStorage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "foudaa@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['storagedriver']
period = 60 * 30  # 30min
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

    module = ''

    def failure(self, msg, test_name=None):
        results.append({'message': msg, 'uid': test_name, 'category': module, 'state': 'ERROR'})

    def success(self, msg, test_name=None):
        results.append({'message': msg, 'uid': test_name, 'category': module, 'state': 'OK'})

    def warning(self, msg, test_name=None):
        results.append({'message': msg, 'uid': test_name, 'category': module, 'state': 'WARNING'})

    HCLogHandler.failure = failure
    HCLogHandler.success = success
    HCLogHandler.warning = warning
    logger = HCLogHandler(print_progress=False)
    results = []

    alba = AlbaHealthCheck()
    alba.module = "Alba Module"
    arakoon = ArakoonHealthCheck()
    arakoon.module = "Arakoon Module"
    ovs = OpenvStorageHealthCheck()
    ovs.module = "OVS Module"
    volumedriver = VolumedriverHealthCheck()
    volumedriver.module = "Volumedriver Module"

    def check_arakoon():
        """
        Checks all critical components of Arakoon
        """
        arakoon.check_arakoons()

    def check_openvstorage():
        """
        Checks all critical components of Open vStorage
        """
        ovs.get_local_settings(logger)
        ovs.check_ovs_workers(logger)
        ovs.check_ovs_packages(logger)
        ovs.check_required_ports(logger)
        ovs.get_zombied_and_dead_processes(logger)
        ovs.check_required_dirs(logger)
        ovs.check_size_of_log_files(logger)
        ovs.check_if_dns_resolves(logger)
        ovs.check_model_consistency(logger)
        ovs.check_for_halted_volumes(logger)
        ovs.check_filedrivers(logger)

    def check_volumedriver():
        volumedriver.check_dtl(logger)
        volumedriver.check_volumedrivers(logger)

    def check_alba():
        """
        Checks all critical components of Alba
        """
        alba.check_alba(logger)

    module = 'OpenvStorage'
    check_openvstorage()
    module = 'Arakoon'
    # check_arakoon()
    module = 'Volumedrver'
    check_volumedriver()
    module = 'Alba'
    check_alba()
    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
