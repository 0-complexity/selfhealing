from JumpScale import j
import os
import sys
import json

descr = """
Checks for stale metadata disks on volume driver nodes.
Inspired by http://pastebin.com/CghxtDHp from Jeffrey Devloo (OVS) <- This link might expire...
"""

organization = 'greenitglobe'
category = "selfhealing"
author = "geert@greenitglobe.com"
version = "1.0"

enable = True
async = True
roles = ['storagedriver']
queue = 'process'

def action():
    sys.path.append('/opt/OpenvStorage')
    import volumedriver.storagerouter.storagerouterclient as src
    from ovs.dal.lists.vpoollist import VPoolList
    from ovs.lib.vdisk import VDiskController
    from ovs.extensions.generic.configuration import Configuration

    osis = j.clients.osis.getNamespace('system')
    accl = j.clients.agentcontroller.get()

    for vpool in VPoolList.get_vpools():
        mountpoint = '/mnt/{0}'.format(vpool.name)
        config_file = Configuration.get_configuration_path('/ovs/vpools/{0}/hosts/{1}/config'.format(vpool.guid, vpool.storagedrivers[0].name))

        client = src.LocalStorageRouterClient(config_file)
        try:
            config = json.loads(client.get_running_configuration())
        except src.ClusterNotReachableException:
            j.errorconditionhandler.raiseOperationalWarning(
                message='%s is offline' % (vpool.name),
                category=category,
                tags='GarbageCollector'
            )
            continue

        cluster_id = str(config['volume_router_cluster']['vrouter_cluster_id'])
        arakoon_cluster_id = str(config['volume_registry']['vregistry_arakoon_cluster_id'])
        arakoon_cluster_nodes = [src.ArakoonNodeConfig(str(node['node_id']), str(node['host']), int(node['port'])) for node in config['volume_registry']['vregistry_arakoon_cluster_nodes']]

        object_registry_client = src.ObjectRegistryClient(cluster_id, arakoon_cluster_id, arakoon_cluster_nodes)
        filesystem_metadata_client = src.FileSystemMetaDataClient(cluster_id, arakoon_cluster_id, arakoon_cluster_nodes)
        cluster_registery = src.ClusterRegistry(cluster_id, arakoon_cluster_id, arakoon_cluster_nodes)
        volume_locations = get_volumes_by_path(mountpoint, filesystem_metadata_client)
        for volume_id, volume_info in volume_locations.iteritems():
            try:
                heal_volume(str(volume_id), volume_info['volume_name'],
                    volume_info['dir'].replace(mountpoint, ''),
                    object_registry_client, filesystem_metadata_client,
                    cluster_registery, vpool.guid, mountpoint, osis, accl)
            except RuntimeError as ex:
                print 'Got {0} while removing. Metadata might not stale for {1}. Remove it using the GUI or API.'.format(str(ex), volume_id)

def heal_volume(volume_id, volume_name, volume_parent_dir, object_registry_client,
                filesystem_metadata_client, cluster_registery, vpool_id, mountpoint,
                osis, accl):
    path = '%s%s%s'%(mountpoint, volume_parent_dir, volume_name)
    found_item = object_registry_client.find(str(volume_id))
    if found_item is None:
        # item not found - stale metadata
        print 'Did not find an entry in the object registry for {0}'.format(volume_name)
        root = filesystem_metadata_client.find_path(volume_parent_dir.rstrip('/'))
        filesystem_metadata_client.unlink(root.object_id(), volume_name)
        j.errorconditionhandler.raiseOperationalWarning(
            message='Deleted stale volume %s ' % (path),
            category=category,
            tags='GarbageCollector'
        )
        return

    try:
        os.stat(path)
    except OSError:
        print "We need to restart volume", path
        volume_node_id = found_item.node_id()
        for node in cluster_registery.get_node_configs():
            if volume_node_id == node.vrouter_id:
                owner_ip = node.xmlrpc_host
                result = osis.node.search({'ipaddr': owner_ip})
                if result[0] != 1:
                    j.errorconditionhandler.raiseOperationalWarning(
                        message='Cloud not find node with ip ' % (owner_ip),
                        category='selfhealing',
                        tags='GarbageCollector'
                    )
                    return
                result = result[1]
                gid = result['gid']
                nid = result['id']
                try:
                    accl.execute('greenitglobe', 'disk_restart', nid=nid, gid=gid,
                                 args=dict(vpool=vpool_id,
                                           storagedriver=volume_node_id,
                                           volume_id=volume_id))
                    print "Volume restarted successfully"
                    j.errorconditionhandler.raiseOperationalWarning(
                        message='Restarted stopped volume %s ' % (volume_name),
                        category='selfhealing',
                        tags='GarbageCollector'
                    )
                except RuntimeError as e:
                    print "Failed to restart the volume"
                    j.errorconditionhandler.raiseOperationalWarning(
                        message='Failed to restarted stopped volume %s\nError: %s' % (volume_name, e),
                        category='selfhealing',
                        tags='GarbageCollector'
                    )
                return

def get_volumes_by_path(mountpoint, filesystem_metadata_client):
    def do(start_path):
        volumes = {}
        for entry in os.listdir(start_path):
            entry_path = '{0}/{1}'.format(start_path, entry)
            if os.path.isdir(entry_path):
                volumes.update(do(entry_path))
            elif entry_path.endswith('.raw'):
                object_id = filesystem_metadata_client.find_path(entry_path[len(mountpoint):]).object_id()
                volumes[object_id] = {'dir': '{0}/'.format(start_path), 'volume_name': entry}
        return volumes
    return do(mountpoint)

if __name__ == '__main__':
    action()
