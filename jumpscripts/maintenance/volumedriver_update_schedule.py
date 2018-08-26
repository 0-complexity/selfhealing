from JumpScale import j

descr = """
Scheduler that runs on controller that executes the volumedriver_update script to update disks edge ip and port in case its storagedriver is changed.
"""
organization = "greenitglobe"
category = "monitor.maintenance"
version = "1.0"
enable = True
async = True
period = 3600  # 1 houre
roles = ["controller"]
queue = "process"
timeout = 3600


def action():
    acl = j.clients.agentcontroller.get()
    acl.executeJumpscript(
        "greenitglobe",
        "volumedriver_update",
        role="storagedriver",
        gid=j.application.whoAmI.gid,
        wait=False,
    )


if __name__ == "__main__":
    action()
