from JumpScale import j
import netaddr
import math
import random

descr = """
Tests network between cpu and storage nodes
Make sure all types of network can reach eachother
Ping nodes for 10 times
When less then 90% produce a warning
When less then 70% procede an error
When timings are more then 10ms produce a warning
When timings are more then 200ms produce am error
Futhermore it makes sure that all nics in network have same MTU
Otherwise produces an error message
"""
organization = "cloudscalers"
author = "deboeckj@greenitglobe.com"
order = 1
enable = True
async = True
log = True
queue = "process"
period = 300
roles = ["storagenode", "storagedriver", "cpunode"]
category = "monitor.healthcheck"
timeout = 60


def updateNetwork(node, networks):
    for netinfo in node:
        if netinfo["name"] == "lo":
            continue
        for ip, cidr in zip(netinfo["ip"], netinfo["cidr"]):
            net = netaddr.IPNetwork("{}/{}".format(ip, cidr)).cidr
            networks.setdefault(net, []).append(ip)
    return networks


def getMTUSubnet(node, networks):
    for netinfo in node:
        if netinfo["name"] == "lo":
            continue
        for ip, cidr in zip(netinfo["ip"], netinfo["cidr"]):
            net = netaddr.IPNetwork("{}/{}".format(ip, cidr)).cidr
            networks.setdefault(net, {}).setdefault(netinfo["mtu"], []).append(ip)
    return networks


def ping(ip):
    # first wake up the network
    j.system.net.ping(ip, 5)
    # check results
    pingresults = j.system.net.ping(ip)
    status = "OK"
    percent = pingresults["percent"]
    avg = pingresults.get("avg", -1)
    msg = "Pingtest to {} successfull".format(ip)
    if percent < 70:
        status = "ERROR"
    elif status < 90:
        status = "WARNING"
    if avg > 10:
        status = "WARNING"
    elif avg > 200:
        status = "ERROR"
    msg = "Ping to {} {}% with average of {} ms".format(
        ip, percent, avg if avg != -1 else "NA"
    )
    uid = "ping {}".format(ip)
    return {"message": msg, "state": status, "category": "Network", "uid": uid}


def action():
    from threading import Thread

    scl = j.clients.osis.getNamespace("system")
    nodes = scl.node.search(
        {
            "gid": j.application.whoAmI.gid,
            "status": "ENABLED",
            "roles": {"$in": roles},
            "id": {"$ne": j.application.whoAmI.nid},
        }
    )[1:]
    networks = {}
    networksmtu = {}
    results = []
    mynode = scl.node.get(j.application.whoAmI.nid)
    for node in nodes:
        updateNetwork(node["netaddr"], networks)
        getMTUSubnet(node["netaddr"], networksmtu)

    def process_network(netinfo):
        if netinfo["name"] == "lo":
            return
        if netinfo["name"] == "docker0":
            return
        if netinfo["name"] == "gw_mgmt":
            return
        if netinfo["name"].startswith("br-"):
            return
        for myip, cidr in zip(netinfo["ip"], netinfo["cidr"]):
            mynet = netaddr.IPNetwork("{}/{}".format(myip, cidr)).cidr
            netresults = []
            iplist = networks.get(mynet)
            mtulist = networksmtu.get(mynet)
            if iplist is not None:
                for ip in random.sample(iplist, int(math.log(len(iplist)) + 1)):
                    netresults.append(ping(ip))
            else:
                uid = "ping {}".format(myip)
                netresults.append(
                    {
                        "message": "Found IP {} ({}) in strange network".format(
                            myip, netinfo["name"]
                        ),
                        "state": "WARNING",
                        "category": "Network",
                        "uid": uid,
                    }
                )
            if mtulist is not None:
                uid = "mtu {}".format(myip)
                if len(mtulist) > 1:
                    msg = "All MTUs in network: {}/{} need to be configured the same\n".format(
                        myip, cidr
                    )
                    for mtu, ips in mtulist.iteritems():
                        msg += "  MTU {} has following IPs: {}\n".format(
                            mtu, ", ".join(ips)
                        )
                    msg = msg.strip()
                    results.append(
                        {
                            "message": msg,
                            "state": "WARNING",
                            "category": "Network",
                            "uid": uid,
                        }
                    )
                else:
                    results.append(
                        {
                            "message": "All MTUs are configured to {} in network: {}/{}".format(
                                mtulist.keys()[0], myip, cidr
                            ),
                            "state": "OK",
                            "category": "Network",
                            "uid": uid,
                        }
                    )

            results.extend(netresults)

    threads = []
    nodechanges = False
    nodenetwork = j.system.net.getNetworkInfo()
    getMTUSubnet(nodenetwork, networksmtu)
    for netinfo in nodenetwork:
        thread = Thread(target=process_network, args=(netinfo,))
        thread.start()
        threads.append(thread)
        for netmodel in mynode.netaddr:
            if netmodel["name"] == netinfo["name"]:
                for cat in ["mtu", "ip"]:
                    if netmodel[cat] != netinfo[cat]:
                        netmodel[cat] = netinfo[cat]
                        nodechanges = True
    if nodechanges:
        scl.node.set(mynode)

    for thread in threads:
        thread.join()
    return results


if __name__ == "__main__":
    import yaml

    print(yaml.dump(action(), default_flow_style=False))
