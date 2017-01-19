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


def action(warntime=300, quarantinetime=600, threshold=0.8):
    import libvirt
    import json
    from CloudscalerLibcloud.utils.Dispatcher import Dispatcher
    
    # (warntimestart, warntime, quarantinetimestart, quarantinetime, quarantinetimelegacy)
    key = "stats:%s_%s:machines.quarantined" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    d = Dispatcher()
    connection = libvirt.open()
    rediscl = j.clients.redis.getByInstance('system')
    cbcl = j.clients.osis.getNamespace('cloudbroker')
    
    # for demo use
    def emailsend(msg):
        # j.clients.email.send(toaddrs, fromaddr, subject, message, files=None)
        print("msg == > ", msg)

    def quarantine(quarantined, vm_dict, qt):
        d.quarantine_vm(domain.UUIDString())
        emailsend('quarantine')
        tags.tagSet("warntimestart", tags.tagGet('warntimestart'))
        tags.tagSet("warntime", warntime)
        tags.tagSet("quarantinetimestart", j.base.time.getTimeEpoch())
        tags.tagSet("quarantinetime", qt)
        if tags.tagExists("quarantinetimelegacy"):
            tags.tagDelete("quarantinetimelegacy")
        tags.tagSet("warned", True)
        vm_dict.tags = str(tags)
        cbcl.vmachine.updateSearch({'id': vm_dict.id}, {'$set': {'tags': str(tags)}})

    def unquaranetine(quarantined, vm_dict):
        emailsend("unquarantine")
        tags.tagDelete("warntimestart")
        tags.tagSet("warntime", tags.tagGet('warntime'))
        tags.tagSet("quarantinetimestart", tags.tagGet('quarantinetimestart'))
        tags.tagSet("quarantinetimelegacy", tags.tagGet('quarantinetime'))
        if tags.tagExists("quarantinetime"):
            tags.tagDelete("quarantinetime")
        if tags.tagExists("warned"):
            tags.tagDelete("warned")
        d.unquarantine_vm(domain.UUIDString())
        vm_dict.tags = str(tags)
        cbcl.vmachine.updateSearch({'id': vm_dict.id}, {'$set': {'tags': str(tags)}})

    def warn(quarantined):
        emailsend("warn")
        tags.tagSet("warntimestart", j.base.time.getTimeEpoch())
        tags.tagSet("warntime", warntime)
        tags.tagSet("quarantinetimestart", 0)
        if tags.tagExists("quarantinetime"):
            tags.tagDelete("quarantinetime")
        if tags.tagExists("quarantinetimelegacy"):
            tags.tagDelete("quarantinetimelegacy")
        tags.tagSet("warned", True)
        vm_dict.tags = str(tags)
        cbcl.vmachine.updateSearch({'id': vm_dict.id}, {'$set': {'tags': str(tags)}})

    # list all vms running in this node
    domains = connection.listAllDomains()
    # list all quarantined
    # check if quartined list exists if not create it
    q_string = rediscl.get(key)
    if q_string:
        quarantined = json.loads(q_string)
    else:
        quarantined = {}

    for domain in domains:
        if not domain.name().startswith("vm-"):
            continue
        domain_id = domain.name().strip('vm-')
        vm_dict = cbcl.vmachine.get(int(domain_id))
        tags = j.core.tags.getObject(vm_dict.tags)
        # calculate cputime_avg
        aggregatorcl = j.tools.aggregator.getClient(rediscl, "%s_%s" % (j.application.whoAmI.gid,
                                                                        j.application.whoAmI.nid))
        stats = aggregatorcl.statGet("machine.CPU.utilisation@virt.%s" % domain_id)
        if not stats:
            continue
        cputime = stats.m_last
        cputime_avg = cputime / 300
        if tags.tagExists('warned'):
            if cputime_avg < threshold:
                if tags.tagExists('quarantinetimestart') and tags.tagGet('quarantinetimestart') != '0':
                    quarantine_timer = j.base.time.getTimeEpoch() - int(tags.tagGet('quarantinetimestart'))
                    if tags.tagExists('quarantinetime') and quarantine_timer >= int(tags.tagGet('quarantinetime')):
                        unquaranetine(quarantined, vm_dict)
                        continue
                    else:
                        continue
            if cputime_avg >= threshold:
                if not tags.tagExists('warntimestart'):
                    warn(quarantined)
                    continue
                warn_timer = j.base.time.getTimeEpoch() - int(tags.tagGet('warntimestart'))
                if warn_timer >= int(tags.tagGet('warntime')):
                    if tags.tagExists('quarantinetimestart') and tags.tagGet('quarantinetimestart') != '0':
                        quarantine_timer = j.base.time.getTimeEpoch() - int(tags.tagGet('quarantinetimestart'))
                        if tags.tagExists('quarantinetime') and quarantine_timer >= int(tags.tagGet('quarantinetime')):
                            unquaranetine(quarantined, vm_dict)
                            continue
                        else:
                            continue
                    else:
                        qt = quarantinetime
                        if tags.tagExists('quarantinetimelegacy'):
                            qt = int(tags.tagGet('quarantinetimelegacy')) * 2
                        quarantine(quarantined, vm_dict, qt)
                        continue
                else:
                    continue
        else:
            warn(quarantined)

if __name__ == '__main__':
    action(warntime=30, quarantinetime=60, threshold=0.001)