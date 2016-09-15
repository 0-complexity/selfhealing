from JumpScale import j
import netaddr
import math
import random
import json
import re
from fabric.network import NetworkError

descr = """
Tests bandwidth between storage nodes, volume drivers and itself

Generates a warning if bandwidth is below 50% of the maximum speed
Generates an error if bandwidth is below 10% of the maximum speed

"""
organization = "cloudscalers"
author = "deboeckj@greenitglobe.com"
order = 1
enable = True
async = True
log = True
queue = 'io'
interval = (2 * j.application.whoAmI.nid) % 30
period = "%s,%s * * * *" % (interval, interval + 30)
roles = ['storagenode', 'storagedriver', 'cpunode']
category = "monitor.healthcheck"


class NetworkPerformance(object):
    def __init__(self):
        self._backplaneNet = None
        self._nic = None
        self._speed = None
        self._runingServer = None
        self.nic = 'backplane1'
        self._nodes = []
        self.scl = j.clients.osis.getNamespace('system')

        # appened opverstorage to python path
        j.system.platform.ubuntu.checkInstall('iperf3', 'iperf3')

    @property
    def backplaneNet(self):
        if not self._backplaneNet:
            ips = j.system.net.getIpAddress(self.nic)
            if not ips:
                return None
            self._backplaneNet = netaddr.IPNetwork("{}/{}".format(ips[0][0], ips[0][1]))
        return self._backplaneNet

    @property
    def speed(self):
        if not self._speed:
            speedfile = '/sys/class/net/%s/speed' % self.nic
            if j.system.fs.exists(speedfile):
                self._speed = int(j.system.fs.fileGetContents(speedfile))
            else:
                # check if its ovs bridge
                ovsconfig = j.system.ovsnetconfig.getConfigFromSystem()
                nics = j.system.process.execute('ovs-vsctl list-ifaces %s' % self.nic)[1].split('\n')
                for nic in nics:
                    if nic in ovsconfig:
                        if ovsconfig[nic]['detail'][0] == 'PHYS':
                            match = re.search('(?P<speed>\d+)', ovsconfig[nic]['detail'][3])
                            self._speed = int(match.group('speed'))
                            break
        return self._speed

    @property
    def nodes(self):
        if not self._nodes:
            nodeips = []
            nodes = self.scl.node.search({'roles': {'$in': roles}})[1:]
            for node in nodes:
                for net in node['netaddr']:
                    for ip in net['ip']:
                        if ip in self.backplaneNet and ip != str(self.backplaneNet.ip):
                            nodeips.append(ip)

            if nodeips:
                self._nodes = random.sample(nodeips, int(math.log(len(nodeips)) + 1))
            else:
                self._nodes = []

        return self._nodes

    def runIperfServer(self):
        j.logger.log('Running iperf server', 1)
        self._runingServer = j.system.process.executeAsync('iperf3', ['-s'])

    def stopIperfServer(self):
        if self._runingServer:
            self._runingServer.kill()

    def getbandwidthState(self, retransmits):
        """
        """
        if retransmits > 1000:
            return 'ERROR'
        elif retransmits > 500:
            return 'WARNING'
        return 'OK'

    def getClusterBandwidths(self):
        final = []
        for ip in self.nodes:
            result = {'category': 'Bandwidth Test'}
            sshclient = j.remote.cuisine.connect(ip, 22)
            sshclient.fabric.api.env['abort_on_prompts'] = True
            sshclient.fabric.api.env['abort_exception'] = RuntimeError
            try:
                j.logger.log('Installing iperf on %s' % ip, 1)
                if not sshclient.command_check('iperf3'):
                    sshclient.run('apt-get install -y iperf3')
                output = sshclient.run('iperf3 -c %s --format m -k 10000 -b 1G -J' % self.backplaneNet.ip)
                try:
                    data = json.loads(output)
                except:
                    result['message'] = 'Failed to parse json data from iperf'
                    result['uid'] = result['message']
                    result['state'] = 'ERROR'
                    final.append(result)
                    continue

                retransmits = data['end']['sum_sent']['retransmits']
                msg = "Retransmitted packages between %s and %s was %d" % (self.backplaneNet.ip, ip, retransmits)
                result['message'] = msg
                result['state'] = self.getbandwidthState(retransmits)
                if result['state'] != 'OK':
                    print(msg)
                    eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=1, type='OPERATIONS')
                    eco.process()
                final.append(result)
            except NetworkError:
                result['state'] = 'ERROR'
                result['message'] = 'Failed to connect to %s' % (ip)
                result['uid'] = result['message']
                final.append(result)
        if not final:
            return [{'message': 'Single node', 'state': 'OK', 'category': 'Bandwidth Test'}]
        return final


def action():
    ovs = NetworkPerformance()
    ovs.runIperfServer()
    results = ovs.getClusterBandwidths()
    ovs.stopIperfServer()
    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
