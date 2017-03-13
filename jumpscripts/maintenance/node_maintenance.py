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
roles = ['master']


def action():
    acl = j.clients.agentcontroller.get()
    sessions = acl.listSessions()
    ccl = j.clients.osis.getNamespace('cloudbroker')
    stacks = ccl.stack.search({'status': 'ENABLED'})[1:]
    pcl = j.clients.portal.getByInstance('main')
    for stack in stacks:
        for key, value in sessions.iteritems():
            if int(key.split('_')[1]) == int(stack['referenceId']):
                ti = int(time.time() - value[0])
                if ti > 300:
                    pcl.actors.cloudbroker.computenode.maintenance(id=stack['id'], gid=stack['gid'], vmaction='move',
                                                                   message='Agent down, putting node into maintenance')
                    eco = j.errorconditionhandler.getErrorConditionObject(msg='Node: %s is put in maintenance mode' % (stack['referenceId']),
                                                                          msgpub='Node: %s is put in maintenance mode' % (stack['referenceId']),
                                                                          category='selfhealing', level=3,
                                                                          type="MONITORING")
                    eco.nid = int(stack['referenceId'])
                    eco.gid = stack['gid']
                    eco.process()


if __name__ == '__main__':
    action()
