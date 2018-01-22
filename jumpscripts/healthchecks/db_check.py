from JumpScale import j

descr = """
Checks status of MongoDB database on Master. If not running an error condition is thrown.
Result will be shown in the "Databases" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
name = 'info_gather_db'
author = "zains@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
timeout = 60
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
    mongo_status = 'MongoDB Status'
    if status['mongodb'] is False:
        j.errorconditionhandler.raiseOperationalCritical('MongoDB halted', 'monitoring', die=False)
        results.append({'message': 'MongoDB halted', 'uid': mongo_status, 'state': 'HALTED', 'category': 'Databases'})
    else:
        results.append({'message': 'MongoDB running', 'uid': mongo_status, 'state': 'OK', 'category': 'Databases'})
    return results


if __name__ == "__main__":
    print(action())
