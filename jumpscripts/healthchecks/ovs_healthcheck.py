descr = """
This healthcheck calls the standard OpenVStorage healthcheck.  This can be found on : https://github.com/openvstorage/openvstorage-health-check

"""

organization = 'cloudscalers'
author = "foudaa@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['storagedriver']
period = 60 * 30  # 30min
timeout = 60 * 5
enable = False
async = True
queue = 'io'
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
    from ovs.extensions.healthcheck.alba.alba_health_check import AlbaHealthCheck
    from ovs.log.healthcheck_logHandler import HCLogHandler

    module = ''

    def failure(self, msg, unattended_mode_name, unattended_print_mode=True):
        results.append({'message': msg, 'uid': unattended_mode_name, 'category': module, 'state': 'ERROR'})

    def success(self, msg, unattended_mode_name, unattended_print_mode=True):
        results.append({'message': msg, 'uid': unattended_mode_name, 'category': module, 'state': 'OK'})

    def warning(self, msg, unattended_mode_name, unattended_print_mode=True):
        results.append({'message': msg, 'uid': unattended_mode_name, 'category': module, 'state': 'WARNING'})

    HCLogHandler.failure = failure
    HCLogHandler.success = success
    HCLogHandler.warning = warning

    results = []

    alba = AlbaHealthCheck()
    alba.module = "Alba Module"
    arakoon = ArakoonHealthCheck()
    arakoon.module = "Arakoon Module"
    ovs = OpenvStorageHealthCheck()
    ovs.module = "OVS Module"

    def check_arakoon():
        """
        Checks all critical components of Arakoon
        """
        arakoon.check_arakoons()

    def check_openvstorage():
        """
        Checks all critical components of Open vStorage
        """
        ovs.get_local_settings()
        ovs.check_ovs_workers()
        ovs.check_ovs_packages()
        ovs.check_required_ports()
        ovs.get_zombied_and_dead_processes()
        ovs.check_required_dirs()
        ovs.check_size_of_log_files()
        ovs.check_if_dns_resolves()
        ovs.check_model_consistency()
        ovs.check_for_halted_volumes()
        ovs.check_filedrivers()
        ovs.check_volumedrivers()

    def check_alba():
        """
        Checks all critical components of Alba
        """
        alba.check_alba()

    module = 'OpenvStorage'
    check_openvstorage()
    module = 'Arakoon'
    # check_arakoon()
    module = 'Alba'
    check_alba()
    return results


if __name__ == '__main__':
    import yaml
    print yaml.dump(action(), default_flow_style=False)
