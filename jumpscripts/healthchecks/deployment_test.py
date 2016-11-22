from JumpScale import j
descr = """
Tests every predefined period (default 30 minutes) whether test VM exists and if exists it tests write speed. Every 24hrs, test VM is recreated.
Result will be shown in the "Deployment Test" section of the Grid Portal / Status Overview / Node Status page.
Generates warning if write speed is lower than 50 MiB / second.
"""

organization = 'cloudscalers'
author = "deboeckj@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['cpunode']
period = 60 * 30  # 30min
timeout = 60 * 5
enable = True
async = True
queue = 'io'
log = True


def action():
    import time
    import re
    import netaddr
    category = 'Deployment Test'
    ACCOUNTNAME = 'test_deployment'
    pcl = j.clients.portal.getByInstance('main')
    ccl = j.clients.osis.getNamespace('cloudbroker')
    loc = ccl.location.search({'gid': j.application.whoAmI.gid})[1]['locationCode']
    CLOUDSPACENAME = loc

    stack = ccl.stack.search({'referenceId': str(j.application.whoAmI.nid), 'gid': j.application.whoAmI.gid})[1]
    if stack['status'] != 'ENABLED':
        return [{'message': 'Disabling test stack is not enabled', 'uid': 'Disabling test stack is not enabled', 'category': category, 'state': 'SKIPPED'}]

    images = []
    if 'images' in stack:
        images = ccl.image.search({'name': 'Ubuntu 16.04 x64', 'id': {'$in': stack['images']}})[1:]
    if not images:
        return [{'message': "Image not available (yet)", 'category': category, 'state': "SKIPPED"}]
    imageId = images[0]['id']

    with ccl.account.lock(ACCOUNTNAME):
        accounts = ccl.account.search({'name': ACCOUNTNAME, 'status': {'$ne': 'DESTROYED'}})[1:]
        if not accounts:
            j.console.echo('Creating Account', log=True)
            accountId = pcl.actors.cloudbroker.account.create(ACCOUNTNAME, 'admin', None)
        else:
            account = accounts[0]
            if account['status'] != 'CONFIRMED':
                return [{'message': "Skipping deployment test account is not enabled.", 'category': category, 'state': "SKIPPED"}]

            j.console.echo('Found Account', log=True)
            accountId = account['id']

    lockname = '%s_%s' % (ACCOUNTNAME, CLOUDSPACENAME)
    with ccl.cloudspace.lock(lockname, timeout=120):
        cloudspaces = ccl.cloudspace.search({'accountId': accountId, 'name': CLOUDSPACENAME,
                                             'gid': j.application.whoAmI.gid,
                                             'status': {'$in': ['VIRTUAL', 'DEPLOYED']}
                                             })[1:]
        if not cloudspaces:
            j.console.echo('Creating CloudSpace', log=True)
            cloudspaceId = pcl.actors.cloudbroker.cloudspace.create(accountId, loc, CLOUDSPACENAME, 'admin')
            cloudspace = ccl.cloudspace.get(cloudspaceId).dump()
        else:
            cloudspace = cloudspaces[0]

        if cloudspace['status'] == 'VIRTUAL':
            j.console.echo('Deploying CloudSpace', log=True)
            pcl.actors.cloudbroker.cloudspace.deployVFW(cloudspace['id'])
            cloudspace = ccl.cloudspace.get(cloudspace['id']).dump()

    size = ccl.size.search({'memory': 512})[1]
    sizeId = size['id']
    diskSize = min(size['disks'])
    timestamp = time.ctime()

    name = '%s on %s' % (timestamp, stack['name'])
    vms = ccl.vmachine.search({'stackId': stack['id'],
                               'cloudspaceId': cloudspace['id'],
                               'status': {'$nin': ['ERROR', 'DESTROYED']}
                               })[1:]
    for vm in vms:
        try:
            if time.time() - vm['creationTime'] > 3600 * 24:
                j.console.echo('Deleting %s' % vm['name'], log=True)
                pcl.actors.cloudapi.machines.delete(vm['id'])
        except Exception as e:
            j.console.echo('Failed to delete vm %s' % e, log=True)
    vms = ccl.vmachine.search({'stackId': stack['id'], 'cloudspaceId': cloudspace['id'], 'status': 'RUNNING'})[1:]
    if vms:
        vmachineId = vms[0]['id']
        vmachine = pcl.actors.cloudapi.machines.get(vmachineId)
        j.console.echo('Found VM %s' % vmachine['name'], log=True)
    else:
        j.console.echo('Deploying VM', log=True)
        vmachineId = pcl.actors.cloudbroker.machine.createOnStack(cloudspaceId=cloudspace['id'], name=name,
                                                                  imageId=imageId, sizeId=sizeId,
                                                                  disksize=diskSize, stackid=stack['id'],
                                                                  datadisks=[10])
        vmachine = pcl.actors.cloudapi.machines.get(vmachineId)
    now = time.time()
    status = 'OK'
    try:
        ip = vmachine['interfaces'][0]['ipAddress']
        while now + 60 > time.time() and ip == 'Undefined':
            j.console.echo('Waiting for IP', log=True)
            time.sleep(5)
            vmachine = pcl.actors.cloudapi.machines.get(vmachineId)
            ip = vmachine['interfaces'][0]['ipAddress']

        j.console.echo('Got IP %s' % ip, log=True)
        publicports = []
        publicport = 0
        for forward in pcl.actors.cloudapi.portforwarding.list(cloudspace['id']):
            if forward['localIp'] == ip and forward['localPort'] == '22':
                publicport = forward['publicPort']
                break
            publicports.append(int(forward['publicPort']))
        if publicport == 0:
            publicport = 2000 + j.application.whoAmI.nid * 100
            while publicport in publicports:
                publicport += 1
            j.console.echo('Creating portforward', log=True)
            pcl.actors.cloudapi.portforwarding.create(
                cloudspace['id'], cloudspace['externalnetworkip'], publicport, vmachineId, 22, 'tcp')

        externalip = str(netaddr.IPNetwork(cloudspace['externalnetworkip']).ip)
        account = vmachine['accounts'][0]
        j.console.echo('Waiting for externalip connection', log=True)
        if not j.system.net.waitConnectionTest(externalip, publicport, 60):
            j.console.echo('Failed to get public connection %s:%s' % (externalip, publicport), log=True)
            status = 'ERROR'
            msg = 'Could not connect to VM over public interface'
            uid = 'Could not connect to VM over public interface'
        else:
            def runtests():
                status = 'OK'
                j.console.echo('Connecting over ssh %s:%s' % (externalip, publicport), log=True)
                connection = j.remote.cuisine.connect(externalip, publicport, account['password'], account['login'])
                connection.user(account['login'])
                connection.fabric.api.env['abort_on_prompts'] = True
                connection.fabric.api.env['abort_exception'] = RuntimeError
                uid = None

                j.console.echo('Running dd', log=True)
                error = ''
                for x in range(5):
                    try:
                        output = connection.sudo("dd if=/dev/zero of=/dev/vdb bs=4k count=128k")
                        break
                    except Exception as error:
                        print("Retrying, Failed to run dd command. Login error? %s" % error)
                        time.sleep(5)
                else:
                    status = "ERROR"
                    msg = "Failed to run dd command. Login error? %s" % error
                    uid = "Failed to run dd command. Login error? %s" % error
                    return status, msg, uid

                try:
                    j.console.echo('Perfoming internet test', log=True)
                    connection.run('ping -c 1 8.8.8.8')
                except:
                    msg = "Could not connect to internet from vm on node %s" % stack['name']
                    uid = "Could not connect to internet from vm on node %s" % stack['name']
                    j.console.echo(msg, log=True)
                    status = 'ERROR'
                    return status, msg, uid

                try:
                    match = re.search('^\d+.*copied,.*?, (?P<speed>.*?)B/s$',
                                      output, re.MULTILINE).group('speed').split()
                    speed = j.tools.units.bytes.toSize(float(match[0]), match[1], 'M')
                    msg = 'Measured write speed on disk was %sMB/s on Node %s' % (speed, stack['name'])
                    j.console.echo(msg, log=True)
                    if speed < 50:
                        status = 'WARNING'
                        uid = 'Measured write speed on disk was so fast on Node %s' % (stack['name'])
                    return status, msg, uid
                except Exception as e:
                    status = 'ERROR'
                    uid = 'Failed to parse dd speed %s' % (stack['name'])
                    msg = "Failed to parse dd speed %s, failed with %s" % (output, e)
                    return status, msg, uid

            status, msg, uid = runtests()
        if status != 'OK':
            eco = j.errorconditionhandler.getErrorConditionObject(
                msg=msg, category='monitoring', level=1, type='OPERATIONS')
            eco.process()
    except:
        j.console.echo('Deleting test vm', log=True)
        pcl.actors.cloudapi.machines.delete(vmachineId)
        j.console.echo('Finished deleting test vm', log=True)
        raise
    return [{'message': msg, 'uid': uid, 'category': category, 'state': status}]

if __name__ == '__main__':
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
