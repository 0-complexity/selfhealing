from JumpScale import j

descr = """
Scheduler that runs on storagemaster to check the dead volumes
"""

organization = "greenitglobe"
author = "ali.chaddad@gig.tech"
version = "1.0"
category = "monitor.healthcheck"

enable = True
async = True
period = 21600  # 6 hrs
roles = ["controller"]
queue = "process"
log = False
timeout = 60


def action():
    acl = j.clients.agentcontroller.get()
    results = []
    job = acl.executeJumpscript(
        "greenitglobe",
        "dead_volumes_check",
        role="storagemaster",
        gid=j.application.whoAmI.gid,
    )
    if job["state"] != "OK":
        results.append(
            {
                "state": "ERROR",
                "category": "Volumedriver",
                "message": "Couldn't check for dead volumes [job | job?id={}]".format(
                    job["guid"]
                ),
            }
        )
    else:
        results.extend(job["result"])

    if not results:
        results.append(
            {
                "state": "OK",
                "category": "Volumedriver",
                "message": "No dead volumes found",
            }
        )
    return results


if __name__ == "__main__":
    j.core.osis.client = j.clients.osis.getByInstance("main")
    print action()
