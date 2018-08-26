
from JumpScale import j

descr = """
Checks if all AYS processes are running.
Throws an error condition for each process that is not running.
Result will be shown in the "AYS Process" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
log = True
queue = "process"
roles = ["node"]


def action():

    # skippingjumpscript for  jsagent  as it is run outside of ays and would crash this jumpscript
    if 1 in j.system.process.getProcessPid("jsagent"):
        return
    results = list()
    for ays in j.atyourservice.findServices():
        if not ays.getProcessDicts():
            continue
        result = dict()
        result["state"] = "OK"
        result["message"] = "Process %s:%s:%s " % (ays.domain, ays.name, ays.instance)
        result["category"] = "AYS Process"
        result["uid"] = "{}:{}:{}".format(ays.domain, ays.name, ays.instance)
        if not ays.actions.check_up_local(ays, wait=False):
            message = "Restarted process %s:%s:%s" % (
                ays.domain,
                ays.name,
                ays.instance,
            )
            eco_tags = j.core.tags.getObject()
            eco_tags.tagSet("domain", ays.domain)
            eco_tags.tagSet("name", ays.name)
            eco_tags.tagSet("instance", ays.instance)
            j.errorconditionhandler.raiseOperationalWarning(
                message=message, category="selfhealing", tags=str(eco_tags)
            )
            ays.start()

            if not ays.actions.check_up_local(ays, wait=True):
                message = "Process %s:%s:%s is halted" % (
                    ays.domain,
                    ays.name,
                    ays.instance,
                )
                j.errorconditionhandler.raiseOperationalWarning(message, "monitoring")
                result["state"] = "HALTED"
                result["message"] = message
        results.append(result)

    return results


if __name__ == "__main__":
    import yaml

    print(yaml.safe_dump(action(), default_flow_style=False))
