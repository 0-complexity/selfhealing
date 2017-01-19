from JumpScale import j
from CloudscalerLibcloud.utils.Dispatcher import Dispatcher

descr = """
Checks average memory and CPU usage/load. If average per hour is higher than expected an error condition is thrown.

For both memory and CPU usage throws WARNING if more than 80% used and throws ERROR if more than 95% used.

Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
author = "tareka@greenitglobe.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 5 * 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = True
queue = 'process'
roles = ['node']


quarantinetime = 60
warntime = 30


def action(warntime=300, quarantinetime=600):
    import libvirt
    import json
    
    d = Dispatcher()
    connection = libvirt.open()
    rediscl = j.clients.redis.getByInstance('system')
    
    # for demo use
    def emailsend(msg):
        print("email==>" + msg)

    def quarantine(quarantined, domain_dict, QT):
        d.quarantine_vm(domain.ID())
        emailsend('quarantine')
        quarantined["%s" % domain.ID()] = (domain_dict[0], warntime, j.base.time.getTimeEpoch(), QT, None)
        rediscl.set(key, json.dumps(quarantined))
    
    def unquaranetine(quarantined, domain_dict):
        emailsend("unquarantine")
        quarantined["%s" % domain.ID()] = (None, domain_dict[1], domain_dict[2], None, domain_dict[3])
        d.unquarantine_vm(domain.ID())
        rediscl.set(key, json.dumps(quarantined))
        
    def warn(quarantined):
        emailsend("warn")
        quarantined["%s" % domain.ID()] = (j.base.time.getTimeEpoch(), warntime, 0, None, None)
        rediscl.set(key, json.dumps(quarantined))

    # list all vms running in this node
    domains = connection.listAllDomains()
    
    # list all quarantined
    key = "stats:%s_%s:machines.quarantined" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    # check if quartined list exists if not create it 
    q_string = rediscl.get(key) if rediscl.get(key) else "{}"
    quarantined = json.loads(q_string.replace("'", '"'))

    for domain in domains:
        # calculate cputime_avg
        aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid,
                                                                        j.application.whoAmI.nid))
        stats = aggregatorcl.statGet("machine.CPU.utilisation@virt.%s" % (j.application.whoAmI.gid,
                                                                          j.application.whoAmI.nid,
                                                                          domain.ID()))
        cputime = stats.m_last
        cputime_avg = cputime / 300

        if cputime_avg >= 0.8:
            if '%s' % domain.ID() in quarantined.keys():
                domain_dict = quarantined["%s" % domain.ID()]
                if not domain_dict[0]:
                    warn(quarantined)
                    continue
                warn_timer = j.base.time.getTimeEpoch() - domain_dict[0]
                if warn_timer >= domain_dict[1]:
                    if domain_dict[2]:
                        quarantine_timer = j.base.time.getTimeEpoch() - domain_dict[2]
                        if quarantine_timer >= domain_dict[3]:
                            unquaranetine(quarantined, domain_dict)
                            continue
                        else:
                            continue
                    else:
                        QT = quarantinetime
                        if domain_dict[4]:
                            QT = domain_dict[4] * 2
                        quarantine(quarantined, domain_dict, QT)
                        continue
                else:
                    continue
            else:
                warn(quarantined)

if __name__ == '__main__':
    import ipdb; ipdb.set_trace()
    action(warntime=30, quarantinetime=60)