from JumpScale import j

descr = """
This script checks the uptime daemon
"""

organization = "jumpscale"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
queue = "process"
period = 10 * 60
timeout = 60
roles = ["cpunode", "storagenode"]


def action(always_restart=False):
    is_active = j.system.platform.ubuntu.statusService
    healthcheck = {"uid": "Uptime Daemon", "category": "Uptime Daemon"}

    if is_active("uptime-daemon"):
        if always_restart:
            j.do.execute("systemctl restart uptime-daemon")
            healthcheck.update(
                {"message": "The uptime daemon had to be restarted", "state": "WARNING"}
            )
        else:
            healthcheck.update({"message": "Uptime daemon is running", "state": "OK"})
    else:
        exitcode, _, _ = j.do.execute("systemctl restart uptime-daemon; sleep 3")
        if exitcode or not is_active("uptime-daemon"):
            healthcheck.update(
                {
                    "message": "The uptime daemon crashed and couldn't restart it again",
                    "state": "ERROR",
                }
            )
        else:
            healthcheck.update(
                {
                    "message": "The uptime daemon crashed and was started again",
                    "state": "ERROR",
                }
            )

    return [healthcheck]


if __name__ == "__main__":
    action()
