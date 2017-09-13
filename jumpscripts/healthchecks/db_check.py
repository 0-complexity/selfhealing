from JumpScale import j

descr = """
Checks status of MongoDB and InfluxDB databases on Master. If not running an error condition is thrown.
Result will be shown in the "Databases" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
name = 'info_gather_db'
author = "zains@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"

async = True
queue = 'process'
roles = ['master']
enable = True
period = 600

log = True


def action():
    osiscl = j.clients.osis.getByInstance('main')
    status = osiscl.getStatus()
    results = list()
    if status['mongodb'] is False:
        j.errorconditionhandler.raiseOperationalCritical('MongoDB halted', 'monitoring', die=False)
        results.append({'message': 'MongoDB halted', 'uid': 'MongoDB halted', 'state': 'HALTED', 'category': 'Databases'})
    else:
        results.append({'message': 'MongoDB running', 'state': 'OK', 'category': 'Databases'})

    if status['influxdb'] is False:
        j.errorconditionhandler.raiseOperationalCritical('InfluxDB halted', 'monitoring', die=False)
        results.append({'message': 'InfluxDB halted', 'uid': 'InfluxDB halted', 'state': 'HALTED', 'category': 'Databases'})
    else:
        results.append({'message': 'InfluxDB is running', 'state': 'OK', 'category': 'Databases'})
    return results


if __name__ == "__main__":
    print(action())
