from JumpScale import j

descr = """
Scheduler that runs on storagemaster to restart the halted volumes automactically
"""

organization = "greenitglobe"
author = "support@gig.tech"
version = "1.0"

enable = True
async = True
period = 21600  # 6 hrs
roles = ["controller"]
queue = "process"
log = False
timeout = 60


def action():
    acl = j.clients.agentcontroller.get()
    acl.executeJumpscript(
        "greenitglobe",
        "restart_halted_volumes",
        role="storagemaster",
        gid=j.application.whoAmI.gid,
        wait=False,
    )


if __name__ == "__main__":
    j.core.osis.client = j.clients.osis.getByInstance("main")
    print action()
