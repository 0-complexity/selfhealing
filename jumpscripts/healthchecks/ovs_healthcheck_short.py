from JumpScale import j

descr = """
Calls the standard Open vStorage health checks, see: https://github.com/openvstorage/openvstorage-health-check
Result will be shown in the "OpenvStorage" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "cloudscalers"
author = "foudaa@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ["storagedriver"]
period = 180
timeout = 60
enable = True
async = True
queue = "process"
log = True


def action():
    from CloudscalerLibcloud import openvstorage

    results = []

    longtests = (
        ("alba", "Alba", ["processes-test", "proxy-port-test"]),
        (
            "ovs",
            "OpenvStorage",
            [
                "memcached-ports-test",
                "nginx-ports-test",
                "processes-test",
                "workers-test",
                "celery-ports-test",
                "verify-rabbitmq-test",
            ],
        ),
        ("arakoon", "Arakoon", ["ports-test", "missing-node-test"]),
    )

    for modulename, category, tests in longtests:
        for test in tests:
            results.extend(openvstorage.run_healthcheck(modulename, test, category))

    return results


if __name__ == "__main__":
    import yaml

    print(yaml.dump(action(), default_flow_style=False))
