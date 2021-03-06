
from JumpScale import j
import requests
import os
import hashlib
import gevent

descr = """
Sync alerta to alerta
"""

organization = "0-complexity"
author = "foudaa@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitor.maintenance"
period = 60
async = True
queue = "process"
roles = ["master"]
enable = True

log = False


def get_alerts(config, envname, headers):
    alerts = []
    status_list = ["open", "ack"]
    for status in status_list:
        try:
            resp = requests.get(
                config["api_url"] + "/alerts",
                params={"environment": envname, "status": status},
                headers=headers,
            )
            if resp.status_code != 200:
                print(
                    "can not get alerts from alert status_code: {}, Response: {}".format(
                        resp.status_code, resp.content
                    )
                )
            else:
                alerts.extend(resp.json()["alerts"])
        except Exception as e:
            print(e)
    return alerts


def create_alert(config, headers, data):
    try:
        resp = requests.post(config["api_url"] + "/alert", json=data, headers=headers)
        if resp.status_code != 201:
            print(
                "can not create alert status_code: {} ,Response: {}".format(
                    resp.status_code, resp.content
                )
            )
    except Exception as e:
        print(e)


def close_alert(config, headers, alert_id):
    try:
        resp = requests.put(
            config["api_url"] + "/alert/{}/status".format(alert_id),
            json={"status": "closed", "text": "closed via call from ovc"},
            headers=headers,
        )
        if resp.status_code != 200:
            print(
                "can not close alert status_code: {} ,Response: {}".format(
                    resp.status_code, resp.content
                )
            )
    except Exception as e:
        print(e)


def action():
    ocl = j.clients.osis.getNamespace("system")
    gids = ocl.grid.list()
    nids = ocl.node.list()
    nodes = ocl.node.search({"$fields": ["nid", "name", "id", "status"]}, size=0)[1:]
    config = j.application.config["system"].get("alerta")
    ok_states = ["OK", "SKIPPED"]
    if not config:
        return
    api_key = config["api_key"]
    headers = {
        "Authorization": "Key {}".format(api_key),
        "Content-type": "application/json",
    }
    alerts_dict = {}
    jobs = []
    health_checks = ocl.health.search({}, size=0)[1:]
    sent_alerts = []
    nodes_cache = {}
    inactive_nodes = []
    not_fixed_alerts = []
    for node in nodes:
        nodes_cache[node["id"]] = node["name"]
        if node.get("status") == "MAINTENANCE":
            inactive_nodes.append(node["id"])
    grid_cache = {}
    for gid in gids:
        grid_cache[gid] = ocl.grid.get(gid).name

    for gid in gids:
        envname = ocl.grid.get(gid).name
        alerts = get_alerts(config, envname, headers)
        for alert in alerts:
            alerts_dict[alert["resource"]] = alert

    for health_check in health_checks:
        envname = grid_cache.get(health_check["gid"])
        nodename = nodes_cache.get(health_check["nid"])
        # if node not active send an alert for this, then close all its alerts
        if health_check["nid"] in inactive_nodes:
            message = "Node in maintenance"
            uid = hashlib.md5("{}_{}".format(nodename, message)).hexdigest()
            if uid in alerts_dict:
                if uid not in not_fixed_alerts:
                    not_fixed_alerts.append(uid)
                continue
            if uid in sent_alerts:
                continue

            data = dict(
                attributes={},
                resource=uid,
                text=message,
                environment=envname,
                service=[nodename],
                tags=[],
                severity="WARNING",
                event="Maintenance",
            )
            jobs.append(gevent.spawn(create_alert, config, headers, data))
            sent_alerts.append(uid)
            continue
        for message in health_check["messages"]:
            if message.get("uid"):
                uid = hashlib.md5(
                    "{}:{}".format(health_check["guid"], message["uid"])
                ).hexdigest()
            else:
                uid = hashlib.md5(
                    "{}:{}:{}".format(
                        health_check["guid"], message["message"], message["category"]
                    )
                ).hexdigest()
            if uid in sent_alerts:
                continue
            if uid in alerts_dict:
                alert = alerts_dict[uid]
                if message["state"] in ok_states:
                    jobs.append(gevent.spawn(close_alert, config, headers, alert["id"]))
                    sent_alerts.append(uid)
                elif (
                    message["state"] != alert["severity"]
                    or message["message"] != alert["text"]
                ):
                    data = dict(
                        attributes={},
                        resource=uid,
                        text=message["message"],
                        environment=envname,
                        service=["{} - {}".format(nodename, health_check["cmd"])],
                        tags=[],
                        severity=message["state"],
                        event=message["category"],
                    )
                    jobs.append(gevent.spawn(create_alert, config, headers, data))
                    sent_alerts.append(uid)
                del alerts_dict[uid]
            else:
                # if state not ok, send alert
                if message["state"] not in ok_states:
                    data = dict(
                        attributes={},
                        resource=uid,
                        text=message["message"],
                        environment=envname,
                        service=["{} - {}".format(nodename, health_check["cmd"])],
                        tags=[],
                        severity=message["state"],
                        event=message["category"],
                    )
                    jobs.append(gevent.spawn(create_alert, config, headers, data))
                    sent_alerts.append(uid)
    # delete not fixed alerts before closing
    for uid in not_fixed_alerts:
        if uid in alerts_dict:
            del alerts_dict[uid]
    # close other unreported alerts
    for nid, alert in alerts_dict.items():
        jobs.append(gevent.spawn(close_alert, config, headers, alert["id"]))
    gevent.joinall(jobs)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", help="Name of vm to delete")
    options = parser.parse_args()
    import yaml

    print(yaml.safe_dump(action(), default_flow_style=False))
