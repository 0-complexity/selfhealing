from JumpScale import j

descr = """
Checks if libvirt still has VMs that are not known by the system. These VMs are called orphan VMs. Takes into account VMs that have been moved to other CPU nodes.
If orphan disks exist, WARNING is shown in the "Orphanage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
category = "monitor.healthcheck"
name = "vm_orphan"
author = "deboeckj@codescalers.com"
version = "1.0"

period = 3600  # 1 hrs
enable = True
async = True
roles = ["cpunode"]
queue = "process"
timeout = 60


def action():
    import libvirt

    nid = j.application.whoAmI.nid
    gid = j.application.whoAmI.gid
    result = []
    pcl = j.clients.portal.getByInstance("main")
    cbcl = j.clients.osis.getNamespace("cloudbroker", j.core.osis.client)
    vcl = j.clients.osis.getNamespace("vfw", j.core.osis.client)
    stacks = cbcl.stack.search(
        {"gid": j.application.whoAmI.gid, "referenceId": str(j.application.whoAmI.nid)}
    )[1:]
    vfws = vcl.virtualfirewall.search(
        {"gid": j.application.whoAmI.gid, "nid": j.application.whoAmI.nid}
    )[1:]
    networkids = {vfw["id"] for vfw in vfws}
    if not stacks:
        return result  # not registered as a stack
    stack = stacks[0]
    invalidstack = stack["status"] != "ENABLED"
    vms = cbcl.vmachine.search(
        {"stackId": stack["id"], "status": {"$ne": "DESTROYED"}}, size=0
    )[1:]
    vmsbyguid = {vm["referenceId"]: vm for vm in vms}
    con = libvirt.open()
    networkorphan = "Found orphan network %s"
    vmorphan = "Killed orphan %s"
    messages = []
    try:
        domains = con.listAllDomains()
        for domain in domains:
            name = domain.name()
            domainuuid = domain.UUIDString()
            print ("Processing {}".format(name))
            if name.startswith("routeros"):
                networkid = int(name.split("_")[-1], 16)
                if invalidstack:
                    # migrate this vm away
                    print (
                        "\tFound RouterOS while stack is in status {} moving it".format(
                            stack["status"]
                        )
                    )
                    vfw = next(
                        iter(vcl.virtualfirewall.search({"id": networkid})[1:]), None
                    )
                    vcl.virtualfirewall.updateSearch(
                        {"guid": vfw["guid"]},
                        {"$set": {"nid": j.application.whoAmI.nid}},
                    )
                    pcl.actors.cloudbroker.cloudspace.moveVirtualFirewallToFirewallNode(
                        int(vfw["domain"])
                    )
                    continue
                if networkid not in networkids:
                    vfw = next(
                        iter(vcl.virtualfirewall.search({"id": networkid})[1:]), None
                    )
                    if vfw:
                        vcl.virtualfirewall.updateSearch(
                            {"guid": vfw["guid"]},
                            {"$set": {"nid": j.application.whoAmI.nid}},
                        )
                    else:
                        messages.append(networkorphan % networkid)
            else:
                if domainuuid not in vmsbyguid:
                    vm = next(
                        iter(cbcl.vmachine.search({"referenceId": domainuuid})[1:]),
                        None,
                    )
                    if vm and vm["status"] in ["DESTROYED", "DELETED"]:
                        try:
                            j.console.warning(
                                "Destroying domain {}".format(domain.name())
                            )
                            eco_tags = j.core.tags.getObject()
                            if domain.ID() != -1:
                                domain.destroy()
                                eco_tags.labelSet("domain.destroy")
                            eco_tags.tagSet("domainname", domain.name())
                            eco_tags.labelSet("domain.undefine")
                            j.errorconditionhandler.raiseOperationalWarning(
                                message="undefine orphan libvirt domain %s on nid:%s gid:%s"
                                % (domain.name(), nid, gid),
                                category="selfhealing",
                                tags=str(eco_tags),
                            )
                        except libvirt.libvirtError:
                            pass
                    elif vm:
                        print ("\tFound vm that should be somewhere else moving it")
                        cbcl.vmachine.updateSearch(
                            {"id": vm["id"]}, {"$set": {"stackId": stack["id"]}}
                        )
                    else:
                        eco = j.errorconditionhandler.getErrorConditionObject(
                            msg=vmorphan % (domain.name()), category="monitoring", level=1, type="OPERATIONS"
                        )
                        eco.process()
                        domain.destroy()
                elif invalidstack:
                    # first update stack info then try to migrate it
                    vm = vmsbyguid[domainuuid]
                    print (
                        "\tFound VM while stack is in status {} moving it".format(
                            stack["status"]
                        )
                    )
                    cbcl.vmachine.updateSearch(
                        {"id": vm["id"]}, {"$set": {"stackId": stack["id"]}}
                    )
                    pcl.actors.cloudbroker.machine.moveToDifferentComputeNode(
                        vm["id"],
                        reason="Found VM on stack in status {}".format(stack["status"]),
                        force=False,
                    )
    finally:
        con.close()

    if messages:
        for message in messages:
            result.append(
                {
                    "state": "WARNING",
                    "category": "Orphanage",
                    "message": message,
                    "uid": message,
                }
            )
        errormsg = "\n".join(messages)
        print (errormsg)
        j.errorconditionhandler.raiseOperationalWarning(
            errormsg, "monitoring", noreraise=True
        )
    else:
        result.append(
            {"state": "OK", "category": "Orphanage", "message": "No orphans found"}
        )

    return result


if __name__ == "__main__":
    import yaml

    j.core.osis.client = j.clients.osis.getByInstance("main")
    print yaml.dump(action(), default_flow_style=False)
