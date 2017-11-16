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
interval = (2 * j.application.whoAmI.nid) % 30
period = "%s,%s * * * *" % (interval, interval + 30)
timeout = 60 * 5
enable = True
async = True
queue = 'process'
log = True


def action():
    import time
    import re
    import netaddr
    category = 'Deployment Test'
    imagename = 'Ubuntu 16.04 x64'
    ACCOUNTNAME = 'test_deployment'
    messages = []
    pcl = j.clients.portal.getByInstance('main')
    ccl = j.clients.osis.getNamespace('cloudbroker')
    loc = ccl.location.search({'gid': j.application.whoAmI.gid})[1]['locationCode']
    CLOUDSPACENAME = loc

    class DeployMentTestFailure(Exception):
        pass

    def check_stack():
        uid = "Stack Status"
        stack = ccl.stack.search({'referenceId': str(j.application.whoAmI.nid), 'gid': j.application.whoAmI.gid})[1]
        if stack['status'] != 'ENABLED':
            msg = 'Disabling test, stack is not enabled'
            messages.append({'message': msg, 'uid': uid, 'category': category, 'state': 'SKIPPED'})
            raise DeployMentTestFailure(msg)
        else:
            messages.append({'message': 'Stack is in status ENABLED', 'uid': uid, 'category': category, 'state': 'OK'})
        return stack

    def get_image(stack):
        images = []
        if 'images' in stack:
            images = ccl.image.search({'name': imagename, 'id': {'$in': stack['images']}})[1:]
            msg = "Found image {}".format(imagename)
            messages.append({'message': msg, 'category': category, 'state': "OK"})
        if not images:
            msg = "Image {} not available on stack".format(imagename)
            messages.append({'message': msg, 'category': category, 'state': "SKIPPED"})
            raise DeployMentTestFailure(msg)
        return images[0]

    def get_account():
        with ccl.account.lock(ACCOUNTNAME):
            accounts = ccl.account.search({'name': ACCOUNTNAME, 'status': {'$ne': 'DESTROYED'}})[1:]
            if not accounts:
                j.console.echo('Creating Account', log=True)
                accountId = pcl.actors.cloudbroker.account.create(ACCOUNTNAME, 'admin', None)
                messages.append({'message': "Created account {}".format(ACCOUNTNAME), 'category': category, 'state': "OK"})
                return accountId
            else:
                account = accounts[0]
                if account['status'] != 'CONFIRMED':
                    msg = "Skipping deployment test account is not enabled."
                    messages.append({'message': msg, 'category': category, 'state': "SKIPPED"})
                    raise DeployMentTestFailure(msg)
                messages.append({'message': "Found account {}".format(ACCOUNTNAME), 'category': category, 'state': "OK"})
                j.console.echo('Found Account', log=True)
                return account['id']

    def get_cloudspace(accountId):
        lockname = '%s_%s' % (ACCOUNTNAME, CLOUDSPACENAME)
        with ccl.cloudspace.lock(lockname, timeout=120):
            cloudspaces = ccl.cloudspace.search({'accountId': accountId, 'name': CLOUDSPACENAME,
                                                 'gid': j.application.whoAmI.gid,
                                                 'status': {'$in': ['VIRTUAL', 'DEPLOYED']}
                                                 })[1:]
            if not cloudspaces:
                j.console.echo('Creating CloudSpace', log=True)
                cloudspaceId = pcl.actors.cloudbroker.cloudspace.create(accountId, loc, CLOUDSPACENAME, 'admin')
                messages.append({'message': "Creating cloudspace {}".format(CLOUDSPACENAME), 'category': category, 'state': "OK"})
                cloudspace = ccl.cloudspace.get(cloudspaceId).dump()
            else:
                messages.append({'message': "Found cloudspace {}".format(CLOUDSPACENAME), 'category': category, 'state': "OK"})
                cloudspace = cloudspaces[0]

            if cloudspace['status'] == 'VIRTUAL':
                j.console.echo('Deploying CloudSpace', log=True)
                pcl.actors.cloudbroker.cloudspace.deployVFW(cloudspace['id'])
                cloudspace = ccl.cloudspace.get(cloudspace['id']).dump()
            return cloudspace

    def get_create_vm(stack, cloudspace, imageId):
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
            deploytime = vms[0]['creationTime'] + 3600 * 24
            messages.append({'category': category,
                             'message': 'VM already deployed redeploying at {{{{ts:{}}}}}'.format(deploytime),
                             'state': 'SKIPPED'})
        else:
            j.console.echo('Deploying VM', log=True)
            from CloudscalerLibcloud.utils import libvirtutil
            con = libvirtutil.LibvirtUtil()
            reserved = con.config.get('reserved_mem')
            total = int(con.memory_usage()[0])/1024
            usage = int(con.memory_usage()[1])/1024
            free = total-usage
            if free <= reserved:
                status = 'WARNING'
                msg = "Faild to create Deployment VM, not enought ram for it"
                messages.append({'message': msg, 'category': category, 'state': status})
                raise DeployMentTestFailure(msg)
            else:
                try:
                    vmachineId = pcl.actors.cloudbroker.machine.createOnStack(cloudspaceId=cloudspace['id'], name=name,
                                                                              imageId=imageId, sizeId=sizeId,
                                                                              disksize=diskSize, stackid=stack['id'],
                                                                              datadisks=[10])
                    vmachine = pcl.actors.cloudapi.machines.get(vmachineId)
                    messages.append({'category': category,
                                     'message': 'VM deyployment',
                                     'state': 'OK'})
                except Exception as e:
                    eco = j.errorconditionhandler.processPythonExceptionObject(e)
                    eco.process()
                    msg = "Failed to create VM [eco|/grid/error condition?id={}]".format(eco.guid)
                    j.errorconditionhandler.parsePythonErrorObject(e)
                    messages.append({'category': category,
                                     'message': msg,
                                     'state': 'ERROR'})
                    raise DeployMentTestFailure(msg)
        return vmachine

    def create_fwd(vmachine, externalip):
        now = time.time()
        try:
            ip = vmachine['interfaces'][0]['ipAddress']
            while now + 180 > time.time() and ip == 'Undefined':
                j.console.echo('Waiting for IP', log=True)
                time.sleep(5)
                vmachine = pcl.actors.cloudapi.machines.get(vmachine['id'])
                ip = vmachine['interfaces'][0]['ipAddress']

            j.console.echo('Got IP %s' % ip, log=True)
            publicports = []
            publicport = 0
            for forward in pcl.actors.cloudapi.portforwarding.list(cloudspace['id']):
                if forward['localIp'] == ip and forward['localPort'] == '22':
                    publicport = forward['publicPort']
                    messages.append({'message': "Found port forward {}".format(publicport),
                                     'category': category, 'state': "OK"})
                    return publicport
                publicports.append(int(forward['publicPort']))
            if publicport == 0:
                publicport = 2000 + j.application.whoAmI.nid * 100
                while publicport in publicports:
                    publicport += 1
                j.console.echo('Creating portforward', log=True)
                pcl.actors.cloudapi.portforwarding.create(cloudspace['id'], cloudspace['externalnetworkip'],
                                                          publicport, vmachine['id'], 22, 'tcp')
                messages.append({'message': "Created port forward {}".format(publicport),
                                 'category': category, 'state': "OK"})
                return publicport
        except Exception as e:
            eco = j.errorconditionhandler.processPythonExceptionObject(e)
            eco.process()
            msg = "Failed to create port forward [eco|/grid/error condition?id={}]".format(eco.guid)
            messages.append({'message': msg, 'category': category, 'state': "ERROR"})
            raise DeployMentTestFailure(msg)

    def wait_for_connection(externalip, publicport):
        if not j.system.net.waitConnectionTest(externalip, publicport, 60):
            msg = 'Could not connect to VM over public interface'
            messages.append({'message': msg, 'category': category, 'state': "ERROR"})
            j.console.echo('Failed to get public connection %s:%s' % (externalip, publicport), log=True)
            raise DeployMentTestFailure(msg)

        msg = 'TCP port {}:{} reachable'.format(externalip, publicport)
        messages.append({'message': msg, 'category': category, 'state': "OK"})

    def execute_ssh_command(connection):
        error = ''
        for x in range(5):
            try:
                connection.sudo("ls")
                messages.append({'message': 'Logged in via SSH and executed command', 'category': category, 'state': "OK"})
                break
            except Exception as error:
                print("Retrying, Failed to run dd command. Login error? %s" % error)
                time.sleep(5)
        else:
            msg = 'Failed to execute SSH command. Login error? %s' % error
            messages.append({'message': msg, 'category': category, 'state': "ERROR"})
            raise DeployMentTestFailure(msg)

    def execute_dd_test(connection):
        output = connection.sudo("timeout 120 dd if=/dev/zero of=/dev/vdb bs=4k count=128k || echo $?")
        if output == '124':  # this means timeout happend
            msg = 'Executing dd command with bs 4k and count 128k failed to execute in 2minutes'
            messages.append({'message': msg, 'category': category, 'state': 'ERROR', 'uid': msg})
        else:
            try:
                match = re.search('^\d+.*copied,.*?, (?P<speed>.*?)B/s$',
                                  output, re.MULTILINE).group('speed').split()
                speed = j.tools.units.bytes.toSize(float(match[0]), match[1], 'M')
                msg = 'Measured write speed on disk was %sMB/s' % (speed)
                uid = 'write test on Node %s' % (stack['name'])
                status = 'OK'
                j.console.echo(msg, log=True)
                if speed < 50:
                    status = 'WARNING'
                messages.append({'message': msg, 'category': category, 'state': status, 'uid': uid})
            except Exception as e:
                status = 'ERROR'
                msg = "Failed to parse dd speed %s, failed with %s" % (output, e)
                messages.append({'message': msg, 'category': category, 'state': status, 'uid': uid})

    def execute_ping_test(connection):
        uid = 'ping public ip'
        try:
            j.console.echo('Perfoming internet test', log=True)
            connection.run('ping -c 1 8.8.8.8')
            messages.append({'message': "Pinged 8.8.8.8 from vm", 'category': category, 'state': 'OK', 'uid': uid})
        except:
            messages.append({'message': 'Failed to ping 8.8.8.8 from vm', 'category': category, 'state': 'ERROR', 'uid': uid})

    try:
        stack = check_stack()
        image = get_image(stack)
        accountId = get_account()
        cloudspace = get_cloudspace(accountId)
        vmachine = get_create_vm(stack, cloudspace, image['id'])
        externalip = str(netaddr.IPNetwork(cloudspace['externalnetworkip']).ip)
        publicport = create_fwd(vmachine, externalip)
        wait_for_connection(externalip, publicport)

        account = vmachine['accounts'][0]
        connection = j.remote.cuisine.connect(externalip, publicport, account['password'], account['login'])
        connection.user(account['login'])
        connection.fabric.api.env['abort_on_prompts'] = True
        connection.fabric.api.env['abort_exception'] = RuntimeError
        execute_ssh_command(connection)
        execute_dd_test(connection)
        execute_ping_test(connection)
    except DeployMentTestFailure:
        pass  # exception is already handled
    except Exception as e:
        eco = j.errorconditionhandler.processPythonExceptionObject(e)
        eco.process()
        msg = "Unexpected error during deployment test [eco|/grid/error condition?id={}]".format(eco.guid)
        messages.append({'message': msg, 'category': category, 'state': "ERROR"})

    return messages


if __name__ == '__main__':
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
