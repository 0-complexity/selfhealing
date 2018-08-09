from JumpScale import j
import time

descr = """
This script puts failed nodes into maintenance
"""

organization = "jumpscale"
author = "chaddada@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
period = 180  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['controller']


def action():
    from urlparse import urlparse
    import socket
    acl = j.clients.agentcontroller.get()
    sessions = acl.listSessions()
    ccl = j.clients.osis.getNamespace('cloudbroker')
    pcl = j.clients.portal.getByInstance('main')
    stacks = ccl.stack.search({'status': {'$in': ['ENABLED', 'ERROR']}, 'gid': j.application.whoAmI.gid})[1:]
    connection_ok = True
    for stack in stacks:
        for key, value in sessions.iteritems():
            if int(key.split('_')[1]) == int(stack['referenceId']):
                ti = int(time.time() - value[0])
                if ti > 120:
                    stack_ip = urlparse(stack['apiUrl']).hostname
                    try:
                        sshclient = j.remote.ssh.getSSHClient(password=None, host=stack_ip)
                        exit_code, _, _ = sshclient.rawExecute(command="ays restart -n jsagent")
                    except socket.error:
                        connection_ok = False
                    if not connection_ok or exit_code != 0:
                        pcl.actors.cloudbroker.node.maintenance(nid=stack['referenceId'], vmaction='move')
                        msg = 'Node: %s is put in maintenance mode' % (stack['referenceId'])
                    else:
                        msg = 'Jsagent for node: %s has been restarted' % (stack['referenceId'])

                    eco = j.errorconditionhandler.getErrorConditionObject(msg=msg,
                                                                          msgpub=msg,
                                                                          category='selfhealing', level=3,
                                                                          type="MONITORING")
                    eco.nid = int(stack['referenceId'])
                    eco.gid = stack['gid']
                    eco.process()


if __name__ == '__main__':
    action()
