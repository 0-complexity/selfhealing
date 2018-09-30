from JumpScale import j
import time
import os


descr = """
Checks the status of our virtual gateways on the node.
"""
organization = "greenitglobe"
author = "deboeckj@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ["cpunode"]
enable = True
async = True
period = 15 * 60  # 15 minutes
timoue = 10 * 60
startup = True
queue = "process"
log = True


def action():
    from CloudscalerLibcloud.gateway import Gateway

    vcl = j.clients.osis.getNamespace("vfw")
    pcl = j.clients.portal.getByInstance("main")
    hcategory = "Network"
    messages = []
    vfws = vcl.virtualfirewall.search(
        {"nid": j.application.whoAmI.nid, "type": "vgw"}, size=0
    )[1:]

    def start_vfw(vfw):
        try:
            print('Starting vfw {:04x}'.format(vfw['id']))
            pcl.actors.cloudbroker.cloudspace.startVFW(int(vfw["domain"]))
        except:
            # we are not handeling the exception as the portal will already have this logged
            link = "[{id}|/cbgrid/private network?id={id}&gid={gid}]".format(**vfw)
            spacelink = "[space|/cbgrid/cloud space?id={id}]".format(id=vfw["domain"])
            message = "Virtual Firewall {link} on {spacelink} died. Tried to start it but the action failed."
            messages.append(
                {
                    "state": "ERROR",
                    "category": hcategory,
                    "message": message.format(link=link, spacelink=spacelink),
                }
            )

    services = {}
    for servicename, status in j.system.platform.ubuntu.listServices().items():
        if servicename.startswith("gw-"):
            services[servicename] = status

    for vfw in vfws:
        gw = Gateway(vfw)
        if not gw.namespace_exists():
            start_vfw(vfw)
            continue

        for service in gw.services:
            servicename = "gw-{:04x}-{}.service".format(vfw["id"], service)
            if servicename not in services:
                # start vfw
                start_vfw(vfw)
            else:
                services.pop(servicename)
                if not gw.service_status(service):
                    messages.append(
                        {
                            "state": "ERROR",
                            "category": hcategory,
                            "message": "Service {} is not running".format(servicename),
                        }
                    )

    for service in services:
        name, _ = os.path.splitext(service)
        j.system.platform.ubuntu.serviceUninstall(name)
        j.errorconditionhandler.raiseOperationalWarning(
            "Cleaned up orphan service {}".format(name), category="selfhealing"
        )
    if not messages:
        messages.append(
            {
                "state": "OK",
                "category": hcategory,
                "message": "All Virtual Firewalls running ok",
            }
        )

    return messages


if __name__ == "__main__":
    import yaml

    print(yaml.safe_dump(action(), default_flow_style=False))
