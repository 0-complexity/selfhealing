from JumpScale import j

descr = """
Collects the fans functionality of a node using ipmitool.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60 # 1min
enable = True
async = True
queue = 'process'
log = True

def action():
    category = "Fans"
    results = []
    rc, _ = j.system.process.execute("which ipmitool", dieOnNonZeroExitCode=False)
    if rc != 0:
        rc, out = j.system.process.execute("""ipmitool sdr type "Fan" """, dieOnNonZeroExitCode=False)
        if out:
            #SAMPLE:
            # root@du-conv-3-01:~# ipmitool sdr type "Fan"
            # FAN1             | 41h | ok  | 29.1 | 5000 RPM
            # FAN2             | 42h | ns  | 29.2 | No Reading
            # FAN3             | 43h | ok  | 29.3 | 4800 RPM
            # FAN4             | 44h | ns  | 29.4 | No Reading

            for line in out.splitlines():
                parts = [part.strip() for part in line.split("|")]
                id_ , sensorstatus, message = parts[0], parts[2], parts[-1]
                if sensorstatus == "ns" and "no reading" in message.lower():
                    results.append(dict(state='SKIPPED', category=category, message="No reading on %s (%s)"%(id_, message)))
                elif sensorstatus != "ok" and "no reading" not in message.lower():
                    results.append(dict(state='WARNING', category=category, message="Fan %s has problem (%s)"%(id_, message)))
                else:
                    results.append(dict(state='OK', category=category, message="(%s) is OK: %s"%(id_, message)))

    return results

if __name__ == '__main__':
    print action()
