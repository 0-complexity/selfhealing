from JumpScale import j

descr = """
Checks cpu time and quratines machine according to fair use policy .

If average per 5 min is higher than threshold a warning is sent via email.

if over use presists for longer than warntime  the machine is quarantined to a limit,
this is done for a quarantine time and then unquarantined .

if quarantined again after unquarantine quarantine time doubles for each time.
"""

organization = "jumpscale"
author = "tareka@greenitglobe.com"
license = "bsd"
version = "1.0"
timeout = 1 * 60
startatboot = True
order = 1
enable = True
async = True
log = True
queue = 'process'
roles = ['master']


def action(recipients, sender='', subject='', message=''):
    import ipdb; ipdb.set_trace()
    nid = j.application.whoAmI.nid
    gid = j.application.whoAmI.gid
    j.clients.email.send(recipients, sender, subject, message)
    j.errorconditionhandler.raiseOperationalWarning(
        message='email has been sent from master node on nid:%s and gid:%s ' % (nid, gid),
        category='info.notify',
        tags='info.emailsend'
    )


if __name__ == '__main__':
    action("tareka@codescalers.com", "support", 'tester', 's')
