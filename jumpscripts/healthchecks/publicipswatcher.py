from JumpScale import j

import netaddr

descr = """
Checks the status of the available public IPs.
Result will be shown in the "Network" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "cloudscalers"
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ["master"]
period = 1800  # 30mins.
enable = True
async = True
queue = "process"
log = True
timeout = 60


def action():
    category = "Network"
    results = []
    account_pool_state = {}
    ccl = j.clients.osis.getNamespace("cloudbroker")
    pools = ccl.externalnetwork.search(query={})[
        1:
    ]  # ignore the count of search result.

    for pool in pools:
        ips = pool["ips"]
        accountId = pool["accountId"]
        ips_count = len(ips)
        usedips_count = ccl.cloudspace.count(
            {"externalnetworkId": pool["id"], "status": "DEPLOYED"}
        )
        for vm in ccl.vmachine.search(
            {"nics.type": "PUBLIC", "status": {"$nin": ["ERROR", "DESTROYED"]}}
        )[1:]:
            for nic in vm["nics"]:
                if nic["type"] == "PUBLIC":
                    tagObj = j.core.tags.getObject(nic["params"])
                    if int(tagObj.tags.get("externalnetworkId", "0")) == pool["id"]:
                        usedips_count += 1

        account_pool_state.setdefault(accountId, {"used": 0, "total": 0})
        account_pool_state[accountId]["used"] += usedips_count
        account_pool_state[accountId]["total"] += usedips_count + ips_count

    for account_id, data in account_pool_state.items():
        percent = (float(data["used"]) / data["total"]) * 100
        accounts = ccl.account.search({"id": account_id})[1:]
        if accounts:
            account = accounts[0]["name"]
        else:
            account = "Default"
        if percent > 95:
            results.append(
                dict(
                    state="ERROR",
                    category=category,
                    message="Used External IPs on account: {name} passed the dangerous threshold. ({percent:.0f}%)".format(
                        name=account, percent=percent
                    ),
                    uid="pub_ips_{}".format(account),
                )
            )
        elif percent > 80:
            results.append(
                dict(
                    state="WARNING",
                    category=category,
                    message="Used External IPs on account: {name} passed the critical threshold. ({percent:.0f}%)".format(
                        name=account, percent=percent
                    ),
                    uid="pub_ips_{}".format(account),
                )
            )

        else:
            results.append(
                dict(
                    state="OK",
                    category=category,
                    message="Used External IPs on account:{name} ({percent:.0f}%)".format(
                        name=account, percent=percent
                    ),
                    uid="pub_ips_{}".format(account),
                )
            )
    return results


if __name__ == "__main__":
    import yaml

    print(yaml.safe_dump(action(), default_flow_style=False))
