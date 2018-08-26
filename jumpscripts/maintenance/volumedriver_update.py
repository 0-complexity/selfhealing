import re
from JumpScale import j

descr = """
Update disks edge ip and port in case its storagedriver is changed.
"""
organization = "greenitglobe"
category = "monitor"
version = "1.0"
enable = True
async = True
roles = ["storagedriver"]
queue = "process"


def get_ovs_client():
    scl = j.clients.osis.getNamespace("system")
    ovs = scl.grid.get(j.application.whoAmI.gid).settings["ovs_credentials"]
    return j.clients.openvstorage.get(
        ovs["ips"], (ovs["client_id"], ovs["client_secret"])
    )


def get_vdisk_guid(referenceId):
    return referenceId[referenceId.rfind("@") + 1 :]


def get_vdisk_storagedriver(ovscl, vdisk, storagedrivers):
    for storagedriver in storagedrivers:
        if (
            storagedriver["storagerouter_guid"] == vdisk["storagerouter_guid"]
            and storagedriver["vpool_guid"] == vdisk["vpool_guid"]
        ):
            return storagedriver


def action():
    ovscl = get_ovs_client()
    ccl = j.clients.osis.getNamespace("cloudbroker")
    storagedrivers = ovscl.get(
        "/storagedrivers", params={"contents": "vpool,storagerouter"}
    )["data"]

    disks = ccl.disk.search({"status": {"$in": ["CREATED", "ASSIGNED"]}}, size=0)[1:]
    for disk in disks:
        guid = get_vdisk_guid(disk["referenceId"])
        vdisk = ovscl.get(
            "/vdisks/{}".format(guid), params={"contents": "vpool,storagerouter_guid"}
        )
        storagedriver = get_vdisk_storagedriver(ovscl, vdisk, storagedrivers)

        disk_url = re.findall(r"[0-9]+(?:\.[0-9]+){3}:[0-9]+", disk["referenceId"])[0]
        vdisk_url = "{}:{}".format(
            storagedriver["cluster_ip"], storagedriver["ports"]["edge"]
        )

        if disk_url != vdisk_url:
            referenceId = disk["referenceId"].replace(disk_url, vdisk_url)
            ccl.disk.updateSearch(
                {"id": disk["id"]}, {"$set": {"referenceId": referenceId}}
            )

            j.errorconditionhandler.raiseOperationalWarning(
                message="Vdisk is moved to storagedriver: {}, the original storagedriver might be down".format(
                    storagedriver["name"]
                ),
                category="storage",
                tags="vdiskguid:{}".format(guid),
            )


if __name__ == "__main__":
    action()
