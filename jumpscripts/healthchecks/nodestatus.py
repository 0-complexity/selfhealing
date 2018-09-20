from JumpScale import j

descr = """
Checks the status of each node.

ERROR state is automatically attributed to a node by OpenvCloud - this is done if a specific action cannot be executed anymore on the Node.

Result will be shown in the "Node Status" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "cloudscalers"
author = "deboeckj@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ["cpunode", "storagenode"]
period = 60 * 5  # 30min
timeout = 60 * 1
enable = True
async = True
queue = "process"
log = True


def action():
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    scl = j.clients.osis.getNamespace("system")
    node = scl.node.searchOne({"id": nid, "gid": gid})
    category = "Node Status"
    if not node:
        hostname = j.system.net.getHostname()
        management_ip = j.system.net.getDefaultIPConfig()[1]
        out = j.system.fs.fileGetContents("/proc/uptime")
        uptime = float(out.strip("\n").split(" ")[0]) / 3600 # uptime in hours

        return [
            {
                "message": "Can not find a node with id {} and gid {}, hostname: {}, management ip: {},  uptime: {:.2f} H".format(nid, gid, hostname, management_ip, uptime),
                "uid": category,
                "category": category,
                "state": "ERROR",
            }
        ]
    if node["status"] == "ERROR":
        return [
            {
                "message": "Node is in error state",
                "uid": category,
                "category": category,
                "state": "ERROR",
            }
        ]
    elif node["status"] == "ENABLED":
        return [
            {
                "message": "Node is enabled",
                "category": category,
                "state": "OK",
                "uid": category,
            }
        ]
    elif node["status"] in ["MAINTENANCE", "DECOMISSIONED"]:
        return [
            {
                "message": "Node state is %s" % node["status"],
                "uid": category,
                "category": category,
                "state": "SKIPPED",
            }
        ]
    else:
        return [
            {
                "message": "Node has an invalid state %s" % node["status"],
                "uid": category,
                "category": category,
                "state": "ERROR",
            }
        ]


if __name__ == "__main__":
    print action()
