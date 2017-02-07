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

MESSAGETYPE = {'error': 'ERROR',
               'success': 'OK',
               'warning': 'WARNING',
               'exception': 'ERROR',
               'skip': 'SKIPPED'}


def action():
    import sys
    sys.path.insert(0, '/opt/OpenvStorage')
    from ovs.extensions.healthcheck.expose_to_cli import HealthCheckCLIRunner
    results = []

    def run(modulename, category):
        try:
            hcresults = HealthCheckCLIRunner.run_method(modulename)
            for testcategory, messageinfo in hcresults['result'].iteritems():
                for state, messages in messageinfo['messages'].iteritems():
                    for message in messages:
                        results.append(dict(state=MESSAGETYPE.get(state),
                                            message=message['message'],
                                            uid=message['message'],
                                            category=category)
                                       )

        except Exception as e:
            raise
            eco = j.errorconditionhandler.processPythonExceptionObject(e)
            msg = 'Failure in check see [eco|/grid/error condition?id={}]'.format(eco.guid)
            results.append({'message': msg, 'category': category, 'state': 'ERROR'})

    run('ovs', 'OpenvStorage')
    run('arakoon', 'Arakoon')
    run('volumedriver', 'Volumedriver')
    run('alba', 'Alba')

    return results


if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
