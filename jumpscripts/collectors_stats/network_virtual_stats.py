from JumpScale import j
import xml.etree.ElementTree

descr = """
Gathers following network statistics from the virtual machines:
  - network.throughput.outgoing
  - network.throughput.incoming
  - network.packets.tx
  - network.packets.rx
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
category = "info.gather.nic"
period = 60  # always in sec
timeout = period * 0.2
enable = True
async = True
queue = "process"
roles = ["cpunode"]
log = False


def calc_network_data(interface_name, interface_type="interface"):
    path = j.system.fs.joinPaths("/sys/class/net", interface_name, "statistics")
    result = {}
    try:
        bytes_sent = int(j.system.fs.fileGetContents(path + "/tx_bytes"))
        bytes_recv = int(j.system.fs.fileGetContents(path + "/rx_bytes"))
        packets_sent = int(j.system.fs.fileGetContents(path + "/tx_packets"))
        packets_recv = int(j.system.fs.fileGetContents(path + "/rx_packets"))
    except IOError as e:
        if e.errno == 2:
            return None
    if interface_type == "routeros":
        result["network.vfw.throughput.outgoing"] = int(
            round(bytes_sent / (1024.0 * 1024), 0)
        )
        result["network.vfw.throughput.incoming"] = int(
            round(bytes_recv / (1024.0 * 1024), 0)
        )
        result["network.vfw.packets.tx"] = packets_sent
        result["network.vfw.packets.rx"] = packets_recv
    else:
        result["network.throughput.outgoing"] = int(
            round(bytes_sent / (1024.0 * 1024), 0)
        )
        result["network.throughput.incoming"] = int(
            round(bytes_recv / (1024.0 * 1024), 0)
        )
        result["network.packets.tx"] = packets_sent
        result["network.packets.rx"] = packets_recv
    return result


def action():
    import libvirt

    connection = libvirt.open()
    vmcl = j.clients.osis.getCategory(j.core.osis.client, "cloudbroker", "vmachine")
    rediscl = j.clients.redis.getByInstance("system")
    aggregatorcl = j.tools.aggregator.getClient(
        rediscl, "%s_%s" % (j.application.whoAmI.gid, j.application.whoAmI.nid)
    )

    # list all vms running in this node
    domains = connection.listAllDomains()

    all_results = {}
    for domain in domains:

        vm = next(iter(vmcl.search({"referenceId": domain.UUIDString()})[1:]), None)
        if vm is None:
            if not domain.name().startswith("routeros"):
                continue
            interfaces_names = []
            tree = xml.etree.ElementTree.fromstring(domain.XMLDesc())
            targets = tree.findall("devices/interface/target")

            for target in targets:
                if not target.attrib["dev"].startswith("gwm"):
                    interfaces_names.append(target.attrib["dev"])

            for interface_name in interfaces_names:
                now = j.base.time.getTimeEpoch()
                result = calc_network_data(interface_name, "routeros")
                if result is None:
                    continue
                all_results["vfw_%s" % (interface_name)] = result

                # send data to aggregator
                for key, value in result.iteritems():
                    key = "%s@virt.%s" % (key, interface_name)
                    tags = "gid:%d nid:%d nic:%s type:virtual" % (
                        j.application.whoAmI.gid,
                        j.application.whoAmI.nid,
                        interface_name,
                    )
                    aggregatorcl.measureDiff(key, tags, value, timestamp=now)

        else:
            for nic in vm["nics"]:
                mac = nic["macAddress"]
                now = j.base.time.getTimeEpoch()
                result = calc_network_data(nic["deviceName"])
                if result is None:
                    continue
                all_results["%s_%s" % (vm["id"], mac)] = result

                # send data to aggregator
                for key, value in result.iteritems():
                    key = "%s@virt.%s" % (key, mac)
                    tags = "gid:%d nid:%d nic:%s mac:%s type:virtual" % (
                        j.application.whoAmI.gid,
                        j.application.whoAmI.nid,
                        nic["deviceName"],
                        mac,
                    )
                    aggregatorcl.measureDiff(key, tags, value, timestamp=now)

    return all_results


if __name__ == "__main__":
    import JumpScale.grid.osis

    j.core.osis.client = j.clients.osis.getByInstance("main")
    results = action()
    import yaml

    print yaml.dump(results)
