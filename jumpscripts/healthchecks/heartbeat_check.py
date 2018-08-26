from JumpScale import j

descr = """
checks nodes heartbeats.
"""

organization = "cloudscalers"
author = "foudaa@greenitglobe.com.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"

async = True
queue = "process"
roles = ["master"]
enable = True
period = 600
timeout = 60

log = True


def _getHeartBeats():
    client = j.clients.agentcontroller.get()
    sessions = client.listSessions()
    heartbeats = list()
    for gidnid, session in sessions.iteritems():
        gid, nid = gidnid.split("_")
        gid, nid = int(gid), int(nid)
        heartbeats.append({"gid": gid, "nid": nid, "lastcheck": session[0]})
    return heartbeats


def action():
    category = "JSAgent"
    results = []
    osiscl = j.clients.osis.getByInstance("main")
    nodecl = j.clients.osis.getCategory(osiscl, "system", "node")
    nodes = nodecl.simpleSearch({})
    nodes_name = {node["id"]: node["name"] for node in nodes}
    nids_active = [node["id"] for node in nodes if node["status"] == "ENABLED"]
    nids_non_ctive = [node["id"] for node in nodes if node["status"] != "ENABLED"]

    heartbeats = _getHeartBeats()
    for heartbeat in heartbeats:
        if (
            heartbeat["nid"] not in nids_active
            and heartbeat["nid"] not in nids_non_ctive
        ):
            results.append(
                {
                    "message": "Found heartbeat node(%s: %s) when not in grid nodes."
                    % (nodes_name[heartbeat["nid"]], heartbeat["nid"]),
                    "state": "ERROR",
                    "category": category,
                    "uid": "heartbeat_%s_%s" % (heartbeat["gid"], heartbeat["nid"]),
                    "nid": heartbeat["nid"],
                }
            )

    nid2hb = dict([(x["nid"], x["lastcheck"]) for x in heartbeats])
    for nid in nids_active:
        if nid in nid2hb:
            lastchecked = nid2hb[nid]
            if not j.base.time.getEpochAgo("-2m") < lastchecked:
                state = "ERROR"
            else:
                state = "OK"
            results.append(
                {
                    "message": "Heartbeat lastchecked {{ts:%s}}" % (lastchecked),
                    "state": state,
                    "category": category,
                    "uid": "heartbeat_%s" % nid,
                    "nid": nid,
                }
            )
        else:
            results.append(
                {
                    "message": "Found heartbeat node when not in grid nodes.",
                    "state": "ERROR",
                    "category": category,
                    "uid": "heartbeat_%s" % nid,
                    "nid": nid,
                }
            )
    return results


if __name__ == "__main__":
    print(action())
