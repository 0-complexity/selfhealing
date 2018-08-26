from JumpScale import j

descr = """
Calls the standard Open vStorage health checks, see: https://github.com/openvstorage/openvstorage-health-check
Result will be shown in the "OpenvStorage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "cloudscalers"
author = "foudaa@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ["controller"]
period = 600
timeout = 60 * 6
enable = True
async = True
queue = "process"
log = True


def action():
    acl = j.clients.agentcontroller.get()
    longtests = (
        ("alba", "Alba", ["backend-test"]),
        ("arakoon", "Arakoon", ["integrity-test"]),
    )
    job = acl.executeJumpscript(
        "cloudscalers",
        "ovs_healthcheck_executor",
        gid=j.application.whoAmI.gid,
        args={"longtests": longtests},
        role="storagedriver",
    )
    if job["state"] != "OK":
        raise RuntimeError("Failed to execute alba checks")
    return job["result"]


if __name__ == "__main__":
    import yaml

    print(yaml.dump(action(), default_flow_style=False))
