from JumpScale import j
from ConfigParser import ConfigParser
from urlparse import urlparse, parse_qsl
from StringIO import StringIO
import subprocess
import time
from datetime import datetime

descr = """
This script collapses arakoon on a daily basis
"""

organization = "jumpscale"
author = "support@gig.tech"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
interval = (j.application.whoAmI.nid) % 7
period = "0 %s * * *" % (interval)
startatboot = False
order = 1
enable = True
async = True
log = True
queue = 'io'
roles = ['storagenode']
logfile = '/var/log/ovs/arakoon_collapse.log'
timeout = 60 * 60 * 2


def systemdProperty(service, property):
    args = ['systemctl', 'show', service, '--property={}'.format(property)]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    proc.wait()
    for line in proc.stdout.readlines():
        key, sep, value = line.partition('=')
        if sep == '=' and key == property:
            return value.strip()
    raise ValueError("Not able to get property {} of services {}".format(property, service))


def execute(args, raiseonexit=False):
    with open(logfile, 'a+') as stderr:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=stderr)
        proc.wait()
        if raiseonexit and proc.returncode != 0:
            raise RuntimeError("Failed to execute {}: stdout: {}".format(
                proc.returncode, proc.stdout.read()))
        return proc.stdout.read(), proc.returncode


def info(msg, depth=0):
    if depth:
        print '  ' * depth,
    j.console.info(msg)


class Arakoon(object):
    def __init__(self, config):
        self.config = config

    def command(self, *args):
        cmd = ['arakoon', '-config', self.config]
        cmd.extend(args)
        return execute(cmd)

    def get_raw(self, key):
        return self.command('--get-raw', key)

    def get_master(self):
        return self.command('--who-master')[0].strip()

    def set(self, key, value):
        self.command('--set', key, value)

    def delete(self, key):
        self.command('--delete', key)


def is_small_cluster(clustername):
    for type_ in ('abm', 'config', 'voldr', 'ovsdb'):
        if type_ in clustername:
            return True
    return False


def action():
    COLLAPSKEY = "opscollapse"
    # make sure logdir exists
    j.system.fs.createDir(j.system.fs.getDirName(logfile))
    now = int(time.time())
    info('Running collapse on all arakoons')
    for service, status in j.system.platform.ubuntu.listServices().items():
        if 'ovs-arakoon' not in service or status != 'enabled':
            continue
        if systemdProperty(service, 'SubState') != 'running':
            continue
        clustername = service[12:-8]  # strip ovs-arakoon and remove .service
        execstart = systemdProperty(service, "ExecStart").split()
        configurl = execstart[execstart.index('-config') + 1]
        node = execstart[execstart.index('--node') + 1]
        configp = urlparse(configurl)
        if configp.scheme == 'arakoon':
            arakooninipath = dict(parse_qsl(configp.query))['ini']
            aracl = Arakoon(arakooninipath)
            clusterconfig = StringIO(aracl.get_raw(configp.path.lstrip('/'))[0])
            cfg = ConfigParser()
            cfg.readfp(clusterconfig)
        else:
            arakooninipath = configp.path
            cfg = ConfigParser()
            cfg.read(arakooninipath)

        info('Checking collapse on {}'.format(clustername))
        tlogdir = cfg.get(node, 'tlog_dir')
        if not j.system.fs.exists(tlogdir):
            j.console.warning('Config path {} does not exists'.format(arakooninipath))
            continue
        nrtlogs = len(j.system.fs.listFilesInDir(tlogdir, filter='*.tlx'))
        if nrtlogs < 10:
            info("Not enough tlx files ({}) skipping collapse".format(nrtlogs), 1)
            continue
        araclient = Arakoon(configurl)
        
        # check if collapsing is happening on another node
        value, exitcode = araclient.get_raw(COLLAPSKEY)
        if exitcode == 2 or (now - int(value) > 3600 * 3):
            # key not found lets set and start
            araclient.set(COLLAPSKEY, str(now))
        else:
            info('Other node is collapsing arakoon', 1)
            continue

        # actual collapsing
        currentmaster = araclient.get_master()
        araip = cfg.get(node, 'ip')
        araport = cfg.get(node, 'client_port')

        if is_small_cluster(clustername):
            info('Small cluster found dropping master', 1)
            execute(['arakoon', '--drop-master', clustername, araip, araport])
            currentmaster = araclient.get_master()

        if currentmaster == node:
            info('Current Master collapsing local', 1)
            araclient.command('--collapse-local', node, '10')
            headsfile = j.system.fs.joinPaths(tlogdir, 'head.db')
            j.system.fs.chown(headsfile, 'ovs')
        else:
            date = datetime.fromtimestamp(now)
            if date.weekday() == 6:
                info('Its sunday lets optimize db', 1)
                execute(['arakoon', '--optimize-db', clustername, araip, araport])
            info('Collapse db', 1)
            execute(['arakoon', '--copy-db-to-head', clustername, araip, araport, '10'])

        araclient.delete(COLLAPSKEY)

            
if __name__ == '__main__':
    action()
