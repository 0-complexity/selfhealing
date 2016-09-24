
from JumpScale import j
import os

descr = """
Delete orphan vm and return diskinfo
"""

organization = "0-complexity"
author = "deboeckj@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitor.maintenance"

async = True
queue = 'hypervisor'
roles = []
enable = True

log = True


def action(vmname):
    from CloudscalerLibcloud.utils.libvirtutil import LibvirtUtil
    libvirtutil = LibvirtUtil()
    try:
        domain = libvirtutil.connection.lookupByName(vmname)
    except:
        return []
    domaindisks = list(libvirtutil.get_domain_disks(domain))
    try:
        print('Destroying VM')
        domain.destroy()
    except:
        pass
    for disk in domaindisks:
        source = disk.find('source')
        filename = os.path.basename(source.attrib['name'] + '.raw')
        host = source.find('host')
        storageip = host.attrib['name']
        con = j.remote.cuisine.connect(storageip, 22)
        con.run('cd /mnt/; find -name "{}" -delete'.format(filename))
    print("Undefining VM")
    domain.undefine()
    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', help='Name of vm to delete')
    options = parser.parse_args()
    import yaml
    print(yaml.safe_dump(action(options.name), default_flow_style=False))
