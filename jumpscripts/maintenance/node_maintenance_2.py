from JumpScale import j
import socket, yaml, time

descr = """
This script puts failed nodes into maintenance
"""

organization = "jumpscale"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
async = True
queue = "process"
timeout = 15 * 60
roles = ["controller"]


def action(nid):
    def get_node_ipaddr(node):
        for nic in node.netaddr:
            if nic["name"] == "backplane1":
                return nic["ip"][0]

    nid = int(nid)
    gid = j.application.whoAmI.gid
    pcl = j.clients.portal.getByInstance("main")
    scl = j.clients.osis.getNamespace("system")
    ccl = j.clients.osis.getNamespace("cloudbroker")
    acl = j.clients.agentcontroller.get()
    node = scl.node.get(nid)
    node_ipaddr = get_node_ipaddr(node)

    try:
        j.remote.ssh.getSSHClient(host=node_ipaddr, password=None, timeout=5)
        acl.executeJumpscript(
            "jumpscale",
            "uptime_daemon",
            gid=gid,
            nid=nid,
            args={"always_restart": True},
        )

    except socket.error:
        settings = scl.grid.get(gid).settings
        if settings.get("enableUptimeMonitor", False):
            pcl.actors.cloudbroker.node.maintenance(
                nid=nid, vmaction="move", offline=True
            )

            while True:
                status = scl.node.get(nid).status
                if status == "MAINTENANCE":
                    break
                else:
                    time.sleep(2)

            if "cpunode" in node.roles:
                pcl.actors.cloudbroker.node.applyIpmiAction(
                    nid=nid, action="force_shutdown"
                )

        msg = "Node %s is down" % node.name
        eco = j.errorconditionhandler.getErrorConditionObject(
            msg=msg, msgpub=msg, category="selfhealing", level=3, type="MONITORING"
        )
        eco.nid = node.id
        eco.gid = node.gid
        eco.process()
