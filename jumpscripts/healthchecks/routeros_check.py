from JumpScale import j
from gevent.pool import Pool
import gevent


descr = """
Checks the status of RouterOS.
Result will be shown in the "Network" section of the Grid Portal / Status Overview / Node Status page.
"""
organization = "greenitglobe"
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor"
roles = ["cpunode"]
enable = True
async = True
queue = "process"
log = True


def action():
    category = "Network"
    ccl = j.clients.osis.getNamespace("cloudbroker")
    cloudspaces = ccl.cloudspace.simpleSearch({"status": "DEPLOYED"})
    pcl = j.clients.portal.getByInstance("main")

    def check_ping(client, ip):
        for _ in range(5):
            if client.ping(ip):
                return True
            gevent.sleep(1)
        return False

    def checkros(c):
        vcl = j.clients.osis.getNamespace("vfw")
        external_network = ccl.externalnetwork.get(c["externalnetworkId"])
        vfwid = "{gid}_{networkId}".format(gid=c["gid"], networkId=c["networkId"])
        roslink = "[{vfwid}|/cbgrid/private network?id={id}&gid={gid}]".format(
            vfwid=vfwid, id=c["networkId"], gid=c["gid"]
        )
        spacelink = "[{name}|/cbgrid/cloud space?id={id}]".format(
            name=c["name"], id=c["id"]
        )
        if not vcl.virtualfirewall.exists(vfwid):
            return dict(
                state="ERROR",
                category=category,
                message="RouterOS {vfwid} doesn't exist on {spacelink}".format(
                    vfwid=vfwid, spacelink=spacelink
                ),
            )
        vfw = vcl.virtualfirewall.get(vfwid)
        if vfw.state == "STOPPED":
            return
        client = None
        try:
            client = j.clients.routeros.get(
                vfw.host, vfw.username, vfw.password, timeout=5
            )
            for ip in external_network.pingips:
                ok = check_ping(client, ip)
                if ok:
                    break
            else:
                return dict(
                    state="ERROR",
                    category=category,
                    message="Couldn't reach network on {roslink} for {spacelink}".format(
                        roslink=roslink, spacelink=spacelink
                    ),
                )
            leases = len(client.do("/ip/dhcp-server/lease/print"))
            if leases > 200:
                return dict(
                    state="WARNING",
                    category=category,
                    message="Running out of leases ({leases}/250) on {roslink} for {spacelink}".format(
                        leases=leases, roslink=roslink, spacelink=spacelink
                    ),
                )
            elif leases >= 250:
                return dict(
                    state="ERROR",
                    category=category,
                    message="All leases are consumed for {spacelink}".format(
                        leases=leases, roslink=roslink, spacelink=spacelink
                    ),
                )

            return None
        except Exception as e:
            print(
                "Failed to connect to {vfwid} {csname} error {err}".format(
                    vfwid=vfwid, csname=c["name"], err=e
                )
            )
            message = "RouterOS {roslink} on {spacelink} died. Tried to restart it. The restart failed in the {action} action."
            try:
                pcl.actors.cloudbroker.cloudspace.stopVFW(c["id"])
            except:
                return dict(
                    state="ERROR",
                    category=category,
                    message=message.format(
                        roslink=roslink, spacelink=spacelink, action="stop"
                    ),
                )
            try:
                pcl.actors.cloudbroker.cloudspace.startVFW(c["id"])
            except:
                return dict(
                    state="ERROR",
                    category=category,
                    message=message.format(
                        roslink=roslink, spacelink=spacelink, action="start"
                    ),
                )
        finally:
            if client:
                client.close()

    pool = Pool(10)
    results = pool.map(checkros, cloudspaces)
    if not any(results):  # all ok.
        results = [dict(state="OK", category=category, message="All RouterOS are OK.")]
    results = [x for x in results if x]  # remove nones.
    return results


if __name__ == "__main__":
    import yaml

    print(yaml.dump(action(), default_flow_style=False))
