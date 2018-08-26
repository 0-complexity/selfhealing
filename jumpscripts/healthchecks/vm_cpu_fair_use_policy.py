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
queue = "process"
roles = ["cpunode"]


def action(warntime=300, quarantinetime=600, threshold=0.8):
    import libvirt
    import json
    from CloudscalerLibcloud.utils.Dispatcher import Dispatcher

    nid = j.application.whoAmI.nid
    gid = j.application.whoAmI.gid

    # (warntimestart, warntime, quarantinetimestart, quarantinetime, quarantinetimelegacy)
    key = "stats:%s_%s:machines.quarantined" % (
        j.application.whoAmI.gid,
        j.application.whoAmI.nid,
    )
    d = Dispatcher()
    rediscl = j.clients.redis.getByInstance("system")
    aggregatorcl = j.tools.aggregator.getClient(
        rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    )
    connection = libvirt.open()
    cbcl = j.clients.osis.getNamespace("cloudbroker")
    ccl = j.clients.osis.getNamespace("system")

    # for demo use
    def emailsend(msg, vm_dict):
        recipients = []
        for ac in vm_dict.acl:
            user = ccl.user.search(ac["userGroupID"])
            recipients += user["emails"]
            pcl = j.clients.portal.getByInstance("main")

        for recipient in recipients:
            pcl.actors.system.emailsender.send(
                sender_email="support@greenitglobe.com",
                receiver_email=recipient,
                subject="cpu fair use alert",
                body=msg,
            )

    def quarantine(quarantined, vm_dict, qt):
        d.quarantine_vm(domain.UUIDString())
        cloudspace = cbcl.cloudspace.get(vm_dict.cloudspaceId)
        eco_tags = j.core.tags.getObject()
        eco_tags.tagSet("machineId", vm_dict.id)
        eco_tags.tagSet("accountId", cloudspace.accountId)
        eco_tags.tagSet("cloudspaceId", cloudspace.id)
        eco_tags.labelSet("vm.quarantine")
        j.errorconditionhandler.raiseOperationalWarning(
            message="quarantine rogue vm %s on nid:%s gid:%s" % (vm_dict.id, nid, gid),
            category="selfhealing",
            tags=str(eco_tags),
        )
        emailsend("machine  %s quarantined " % vm_dict.id, vm_dict)
        tags.tagSet("warntimestart", tags.tagGet("warntimestart"))
        tags.tagSet("quarantinetimestart", j.base.time.getTimeEpoch())
        tags.tagSet("quarantinetime", qt)
        if tags.tagExists("quarantinetimelegacy"):
            tags.tagDelete("quarantinetimelegacy")
        tags.tagSet("warned", True)
        vm_dict.tags = str(tags)
        cbcl.vmachine.updateSearch({"id": vm_dict.id}, {"$set": {"tags": str(tags)}})

    def unquaranetine(quarantined, vm_dict):
        emailsend("unquarantine of machine %s " % vm_dict.id, vm_dict)
        tags.tagDelete("warntimestart")
        tags.tagSet("quarantinetimestart", tags.tagGet("quarantinetimestart"))
        tags.tagSet("quarantinetimelegacy", tags.tagGet("quarantinetime"))
        if tags.tagExists("quarantinetime"):
            tags.tagDelete("quarantinetime")
        if tags.tagExists("warned"):
            tags.tagDelete("warned")
        d.unquarantine_vm(domain.UUIDString())
        cloudspace = cbcl.cloudspace.get(vm_dict.cloudspaceId)
        eco_tags = j.core.tags.getObject()
        eco_tags.tagSet("machineId", vm_dict.id)
        eco_tags.tagSet("accountId", cloudspace.accountId)
        eco_tags.tagSet("cloudspaceId", cloudspace.id)
        eco_tags.labelSet("vm.unquarantine")
        j.errorconditionhandler.raiseOperationalWarning(
            message="unquarantine behaving vm %s on nid:%s gid:%s"
            % (vm_dict.id, nid, gid),
            category="selfhealing",
            tags=str(eco_tags),
        )
        vm_dict.tags = str(tags)
        cbcl.vmachine.updateSearch({"id": vm_dict.id}, {"$set": {"tags": str(tags)}})

    def warn(quarantined, vm_dict):
        emailsend(
            "warning threshold cputime passed on machine  %s " % vm_dict.id, vm_dict
        )
        tags.tagSet("warntimestart", j.base.time.getTimeEpoch())
        tags.tagSet("quarantinetimestart", 0)
        if tags.tagExists("quarantinetime"):
            tags.tagDelete("quarantinetime")
        if tags.tagExists("quarantinetimelegacy"):
            tags.tagDelete("quarantinetimelegacy")
        tags.tagSet("warned", True)
        vm_dict.tags = str(tags)
        cbcl.vmachine.updateSearch({"id": vm_dict.id}, {"$set": {"tags": str(tags)}})

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
        if not domain.name().startswith("vm-") or domain.state()[0] != 1:
            continue
        domain_id = domain.name().strip("vm-")
        vms = cbcl.vmachine.search({"referenceId": domain.UUIDString()})[1:]
        if not vms:
            continue
        vm_dict = cbcl.vmachine.new()
        vm_dict.load(vms[0])
        tags = j.core.tags.getObject(vm_dict.tags)
        # calculate cputime_avg

        stats = aggregatorcl.statGet("machine.CPU.utilisation@virt.%s" % domain_id)
        if not stats:
            continue

        cputime = stats.m_last
        cputime_avg = cputime / 300
        if not tags.tagExists("warned"):
            if cputime_avg >= threshold:
                warn(quarantined, vm_dict)
            continue

        if cputime_avg < threshold:
            if (
                tags.tagExists("quarantinetimestart")
                and tags.tagGet("quarantinetimestart") != "0"
            ):
                quarantine_timer = j.base.time.getTimeEpoch() - int(
                    tags.tagGet("quarantinetimestart")
                )
                if tags.tagExists("quarantinetime") and quarantine_timer >= int(
                    tags.tagGet("quarantinetime")
                ):
                    unquaranetine(quarantined, vm_dict)
            continue

        warn_timer = j.base.time.getTimeEpoch() - int(tags.tagGet("warntimestart"))
        if warn_timer < warntime:
            continue

        if (
            tags.tagExists("quarantinetimestart")
            and tags.tagGet("quarantinetimestart") != "0"
        ):
            quarantine_timer = j.base.time.getTimeEpoch() - int(
                tags.tagGet("quarantinetimestart")
            )
            if tags.tagExists("quarantinetime") and quarantine_timer >= int(
                tags.tagGet("quarantinetime")
            ):
                unquaranetine(quarantined, vm_dict)
        else:
            qt = quarantinetime
            if tags.tagExists("quarantinetimelegacy"):
                qt = int(tags.tagGet("quarantinetimelegacy")) * 2
            quarantine(quarantined, vm_dict, qt)


if __name__ == "__main__":
    action(warntime=30, quarantinetime=60, threshold=0.001)
