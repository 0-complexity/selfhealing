from JumpScale import j

descr = """
Checks the power redundancy of a node using ipmitool.
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
    results = []
    rc, _ = j.system.process.execute("which ipmitool", dieOnNonZeroExitCode=False)
    #command doesn't exist.
    if rc != 0:
        #rc, out = j.system.process.execute(""" ipmitool -c sdr type "Power Supply" | awk 'BEGIN {FS=","; OFS=":"}; { print $1, $3}'""",dieOnNonZeroExitCode=False)
        rc, out = j.system.process.execute("""ipmitool -c sdr type "Power Supply" """, dieOnNonZeroExitCode=False)
        if out:
            # SAMPLE:
            # root@du-conv-3-01:~# ipmitool -c sdr type "Power Supply"
            # PS1 Status,C8h,ok,10.1,Presence detected
            # PS2 Status,C9h,ok,10.2,Presence detected
            for line in out.splitlines():
                parts = [part.strip() for part in line.split(",")]
                id_ , status = parts[0] , parts[2]
                if status != "ok"
                    results.append(dict(state='WARNING', category=category, message="Power redundancy problem on %s"%id_ ))
                else:
                    results.append(dict(state='OK', category=category, message="No power redundancy"))
    return results

if __name__ == '__main__':
    print action()
