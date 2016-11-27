from JumpScale import j
descr = """
"""

organization = 'greenitglobe'
author = "tareka@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['master']
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
    now = j.base.time.getTimeEpoch()

    for cs in ccl.cloudspace.search({"status": {'$in': ['DEPLOYING', 'VIRTUAL']}})[1:]:
        vfwid = '{gid}_{networkId}'.format(**cs)
        redeploy = False
        if cs['status'] == 'DEPLOYING':
            if vcl.virtualfirewall.exists(vfwid):
                vfw = vcl.virtualfirewall.get(vfwid)
                job = next(iter(scl.job.search({"guid": vfw.deployment_jobguid})[1:]), None)

                # time out if bigger than 5 min , start self heal
                if job is None or (now - job["timeCreate"]) > 300:
                    redeploy = True
            else:
                redeploy = True
        elif cs['status'] == 'VIRTUAL' and now - cs['creationTime'] > 300:
            redeploy = True
        if redeploy:
            if cs['status'] == 'DEPLOYING':
                ccl.cloudspace.updateSearch({'id': cs['id']}, {'$set': {'status': 'VIRTUAL'}})
            pcl = j.clients.portal.getByInstance('cloudbroker')
            try:
                pcl.actors.cloudapi.cloudspaces.deploy(cs["id"])
            except Exception as e:
                j.errorconditionhandler.processPythonExceptionObject(e)


if __name__ == '__main__':
    action()
