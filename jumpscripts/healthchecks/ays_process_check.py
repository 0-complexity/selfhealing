
from JumpScale import j

descr = """
Checks if all AYS processes are running.
Result will be shown in the "AYS Process" section of the Grid Portal / Status Overview / Node Status page.
Throws an error condition for each process that is not running.
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
log = True
queue = 'process'
roles = ['node']


def action():
    results = list()
    for ays in j.atyourservice.findServices():
        if not ays.getProcessDicts():
                continue
        result = dict()
        result['state'] = 'OK'
        result['message'] = "Process %s:%s:%s " % (ays.domain, ays.name, ays.instance)
        result['category'] = 'AYS Process'
        if not ays.actions.check_up_local(ays, wait=False):
            message = "Process %s:%s:%s is halted" % (ays.domain, ays.name, ays.instance)
            j.errorconditionhandler.raiseOperationalWarning(message, 'monitoring')
            result['state'] = 'HALTED'
            result['message'] = message
            result['uid'] = message
            result['category'] = 'AYS Process'
        results.append(result)

    return results

if __name__ == '__main__':
    action()
