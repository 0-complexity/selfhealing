from JumpScale import j

descr = """
Checks the power redundancy of a node using IPMItool.
Result will be shown in the "Hardware" section of the Grid Portal / Status Overview / Node Status page.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60  # 1min
enable = True
async = True
queue = 'process'
log = True


def action():
    category = "Hardware"
    results = []
    if j.system.platformtype.isVirtual():
        return results
    ps_errmsgs = """
Power Supply AC lost
Failure detected
Predictive failure
AC lost or out-of-range
AC out-of-range, but present
Config Error
Power Supply Inactive
    """.splitlines()
    ps_errmsgs = [x.lower() for x in ps_errmsgs if x.strip()]
    linehaserrmsg = lambda line: any([x in line for x in ps_errmsgs])
    rc, out = j.system.process.execute("""ipmitool -c sdr type "Power Supply" """, dieOnNonZeroExitCode=False)
    if rc != 127:
        if out:
            # SAMPLE 1:
            # root@du-conv-3-01:~# ipmitool -c sdr type "Power Supply"
            # PS1 Status,C8h,ok,10.1,Presence detected
            # PS2 Status,C9h,ok,10.2,Presence detected

            # SAMPLE 2:
            # root@stor-04:~# ipmitool -c sdr type "Power Supply"
            # PSU1_Status,DEh,ok,10.1,Presence detected
            # PSU2_Status,DFh,ns,10.2,No Reading
            # PSU3_Status,E0h,ok,10.3,Presence detected
            # PSU4_Status,E1h,ns,10.4,No Reading
            # PSU Redundancy,E6h,ok,21.1,Fully Redundant

            # SAMPLE 3:
            # root@stor-01:~# ipmitool -c sdr type "Power Supply"
            # PSU1_Status,DEh,ok,10.1,Presence detected, Power Supply AC lost
            # PSU2_Status,DFh,ns,10.2,No Reading
            # PSU3_Status,E0h,ok,10.3,Presence detected
            # PSU4_Status,E1h,ok,10.4,Presence detected
            # PSU Redundancy,E6h,ok,21.1,Redundancy Lost
            # PSU Alert,16h,ns,208.1,Event-Only

            psu_redun_in_out = "PSU Redundancy".lower() in out.lower()
            is_fully_redundant = True if "fully redundant" in out.lower() else False
            for line in out.splitlines():
                if "status" in line.lower():
                    parts = [part.strip() for part in line.split(",")]
                    id_, presence = parts[0], parts[-1]
                    id_ = id_.strip("Status").strip("_").strip()  # clean the power supply name.
                    if linehaserrmsg(line):
                        if psu_redun_in_out and is_fully_redundant:
                            results.append(dict(state='SKIPPED', category=category, uid=id_, message="Power redundancy problem on %s (%s)" % (id_, presence)))
                        else:
                            results.append(dict(state='WARNING', category=category, uid=id_, message="Power redundancy problem on %s (%s)" % (id_, presence)))
            if len(results) == 0:
                results.append(dict(state='OK', category=category, message="Power supplies are OK"))

    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
