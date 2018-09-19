from JumpScale import j

descr = """
This script is to check for dead volumes
"""

organization = "greenitglobe"
author = "ali.chaddad@gig.tech"
version = "1.0"
category = "healthcheck"
timeout = 600
startatboot = False
order = 1
enable = True
async = True
queue = "process"
log = True
roles = ["storagemaster"]


def action():
    import sys
    import re

    sys.path.insert(0, "/opt/OpenvStorage")
    from ovs.dal.lists.vdisklist import VDiskList

    results = []
    ccl = j.clients.osis.getNamespace("cloudbroker")
    vdisks = VDiskList.get_vdisks()

    for vdisk in vdisks:
        if not vdisk.edge_clients:
            name = vdisk.name
            match = re.match("vm-(?P<id>\d+).", name)
            if match:
                machine = ccl.vmachine.searchOne({"id": int(match.group("id"))})
                if not machine or machine["status"] == "RUNNING":
                    results.append(
                        {
                            "state": "WARNING",
                            "category": "Volumedriver",
                            "message": "Found dead disk: {} with guid: {}".format(
                                name, vdisk.guid
                            ),
                            "uid": name,
                        }
                    )
    return results


if __name__ == "__main__":
    print(action())
