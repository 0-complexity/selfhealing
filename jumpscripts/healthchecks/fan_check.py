from JumpScale import j

descr = """
Checks the fans of a node using IPMItool.
Result will be shown in the "Hardware" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = "cloudscalers"
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ["node"]
period = 60 * 5
enable = True
async = True
queue = "process"
log = True
timeout = 20


def action():
    category = "Hardware"
    results = []
    if j.system.platformtype.isVirtual():
        return results
    rc, out = j.system.process.execute(
        """ipmitool sdr type "Fan" """, dieOnNonZeroExitCode=False, noDuplicates=True
    )
    if rc == 0:  # 127 is command not found
        if out:
            # SAMPLE:
            # root@du-conv-3-01:~# ipmitool sdr type "Fan"
            # FAN1             | 41h | ok  | 29.1 | 5000 RPM
            # FAN2             | 42h | ns  | 29.2 | No Reading
            # FAN3             | 43h | ok  | 29.3 | 4800 RPM
            # FAN4             | 44h | ns  | 29.4 | No Reading

            for line in out.splitlines():
                if "|" in line:
                    parts = [part.strip() for part in line.split("|")]
                    id_, sensorstatus, message = parts[0], parts[2], parts[-1]
                    if sensorstatus == "ns" and "no reading" in message.lower():
                        results.append(
                            dict(
                                state="SKIPPED",
                                category=category,
                                uid=id_,
                                message="Fan %s has no reading (%s)" % (id_, message),
                            )
                        )
                    elif sensorstatus != "ok" and "no reading" not in message.lower():
                        results.append(
                            dict(
                                state="WARNING",
                                category=category,
                                uid=id_,
                                message="Fan %s has problem (%s)" % (id_, message),
                            )
                        )
            if len(results) == 0:
                results.append(
                    dict(state="OK", category=category, message="All fans are OK")
                )
    else:
        results.append(
            dict(
                state="SKIPPED",
                category=category,
                message="NO fan information available",
            )
        )

    return results


if __name__ == "__main__":
    print(action())
