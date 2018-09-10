from JumpScale import j

descr = """
Check if number of disks exceeded 6 times machines
"""

organization = "cloudscalers"
name = "vm_disk_ratio"
author = "foudaa@greenitglobe.com"
version = "1.0"
category = "monitor"
queue = "process"
enable = True
async = True
roles = ["storagedriver"]


def action(gid=None):
    scl = j.clients.osis.getNamespace("system")
    cbcl = j.clients.osis.getNamespace("cloudbroker")
    ovs = scl.grid.get(j.application.whoAmI.gid).settings["ovs_credentials"]
    ovscl = j.clients.openvstorage.get(
        ovs["ips"], (ovs["client_id"], ovs["client_secret"])
    )

    result = dict()
    result["state"] = "OK"
    result["category"] = "VMs-Disks ratio"
    result["uid"] = "vm_disk_ratio"

    vmachines_count = cbcl.vmachine.count({"status": {"$nin": ["ERROR", "DESTROYED"]}})
    disks_count = len(ovscl.get("/vdisks", params={})["data"])
    if vmachines_count > 0 and disks_count > 100:
        ratio = round(disks_count / float(vmachines_count), 2)
        if ratio >= 6:
            result["message"] = "Disks to VMs ratio is {ratio}".format(ratio=ratio)
            result["state"] = "WARNING"
        else:
            result["message"] = "Disks to VMs ratio is {ratio}".format(ratio=ratio)
    else:
        result["state"] = "SKIPPED"
        result["message"] = "No machines found"
    return [result]


if __name__ == "__main__":
    action()
