from JumpScale import j
descr = """
"""

organization = 'greenitglobe'
author = "tareka@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['cpunode']
period = 60 * 10  # 10min
timeout = 60 * 5
enable = True
async = True
queue = 'io'
log = True


def action():
        ccl = j.clients.osis.getNamespace('cloudbroker')
        vcl = j.clients.osis.getNamespace('vfw')
        scl = j.clients.osis.getNamespace('system')

        for cs in ccl.cloudspace.search({"status": "DEPLOYING"})[1:]:
            vfwid = '{gid}_{networkId}'.format(**cs)
            redeploy = False
            if vcl.virtualfirewall.exists(vfwid):
                vfw = vcl.virtualfirewall.get(vfwid)
                job = next(iter(scl.job.search({"guid": vfw.deployment_jobguid})[1:]), None)

                # time out if bigger than 5 min , start self heal
                if job is None or (j.base.time.getTimeEpoch() - job["createTime"]) > 300:
                    redeploy = True
            else:
                redeploy = True
            if redeploy:
                cs['status'] = "VIRTUAL"
                ccl.cloudspace.set(cs)
                pcl = j.clients.portal.getByInstance('cloudbroker')
                pcl.actors.cloudapi.cloudspaces.deploy(cs["id"])
