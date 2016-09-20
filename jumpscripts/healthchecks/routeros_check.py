from JumpScale import j
from multiprocessing import Pool


descr = """
Checks the status of RouterOS.
"""
organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['master']
period = 60  # 1min.
enable = True
async = True
queue = 'process'
log = True


def checkros(c):
    rosip = c.get("publicipaddress").split("/")[0]
    cmd = "nc -zv {rosip} 9022".format(rosip=rosip)
    rc, out = j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
    if rc != 0:
        return dict(state='ERROR', category=category, message="RouterOS died on {csname}".format(csname=c.name))
    else:
        return None


def action():
    category = "Network"
    ccl = j.clients.osis.getNamespace('cloudbroker')
    cloudspaces = ccl.cloudspace.simpleSearch({'status': 'DEPLOYED'})
    pool = Pool(10)
    results = pool.map(checkros, cloudspaces)
    if not any(results):  # all ok.
        results = [dict(state='OK', category=category, message="All RouterOS are OK.")]
    return results

if __name__ == "__main__":
    print action()
