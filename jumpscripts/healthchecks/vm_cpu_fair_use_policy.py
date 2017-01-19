from JumpScale import j

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
    from CloudscalerLibcloud.utils.Dispatcher import Dispatcher
    
    # (warntimestart, warntime, quarantinetimestart, quarantinetime, quarantinetimelegacy)
    key = "stats:%s_%s:machines.quarantined" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    d = Dispatcher()
    connection = libvirt.open()
    rediscl = j.clients.redis.getByInstance('system')
    
    # for demo use
    def emailsend(msg):
        j.clients.email.send(toaddrs, fromaddr, subject, message, files=None)

    def quarantine(quarantined, domain_dict, qt):
        d.quarantine_vm(domain.ID())
        emailsend('quarantine')
        quarantined[domain_id] = {"warntimestart": domain_dict['warntimestart'], "warntime": warntime,
                                  "quarantinetimestart": j.base.time.getTimeEpoch(), "quarantinetime": qt,
                                  "quarantinetimelegacy": None}
        rediscl.set(key, json.dumps(quarantined))
    
    def unquaranetine(quarantined, domain_dict):
        emailsend("unquarantine")
        quarantined[domain_id] = {"warntimestart": None, "warntime": domain_dict['warntime'],
                                  "quarantinetimestart": domain_dict['quarantinetimestart'],
                                  "quarantinetime": None, "quarantinetimelegacy": domain_dict['quarantinetimelegacy']}
        d.unquarantine_vm(domain.ID())
        rediscl.set(key, json.dumps(quarantined))
        
    def warn(quarantined):
        emailsend("warn")
        quarantined[domain_id] = {"warntimestart": j.base.time.getTimeEpoch(), "warntime": warntime,
                                  "quarantinetimestart": 0, "quarantinetime": None, "quarantinetimelegacy": None}
        rediscl.set(key, json.dumps(quarantined))

    # list all vms running in this node
    domains = connection.listAllDomains()
    
    # list all quarantined
    # check if quartined list exists if not create it
    q_string = rediscl.get(key)
    if q_string != '':
        quarantined = json.loads(q_string)
    else:
        quarantined = {}

    for domain in domains:
        domain_id = str(domain.ID())
        # calculate cputime_avg
        aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid,
                                                                        j.application.whoAmI.nid))
        stats = aggregatorcl.statGet("machine.CPU.utilisation@virt.%s" % (j.application.whoAmI.gid,
                                                                          j.application.whoAmI.nid,
                                                                          domain_id))
        cputime = stats.m_last
        cputime_avg = cputime / 300

        if cputime_avg >= 0.8:
            if '%s' % domain.ID() in quarantined.keys():
                domain_dict = quarantined[domain_id]
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
                        qt = quarantinetime
                        if domain_dict[4]:
                            qt = domain_dict[4] * 2
                        quarantine(quarantined, domain_dict, qt)
                        continue
                else:
                    continue
            else:
                warn(quarantined)

if __name__ == '__main__':
    import ipdb; ipdb.set_trace()
    action(warntime=30, quarantinetime=60)