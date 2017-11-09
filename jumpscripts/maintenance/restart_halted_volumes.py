from JumpScale import j
descr = """
This script to restart halted volumes
"""

organization = 'greenitglobe'
author = "support@gig.tech"
version = "1.0"
category = "monitor.maintenance"
timeout = 600
startatboot = False
order = 1
enable = True
async = True
queue = 'process'
log = True
roles = ['storagemaster', ]


def action():
    import sys
    sys.path.insert(0, '/opt/OpenvStorage')
    from ovs.extensions.healthcheck.expose_to_cli import HealthCheckCLIRunner
    from ovs.dal.lists.vdisklist import VDiskList

    x = HealthCheckCLIRunner.run_method('volumedriver', 'halted-volumes-test')

    for disk in x['result']['volumedriver-halted-volumes-test']['messages']['error']:
        ids = disk['message'].split(':')[-1]
        for my_id in ids.split(","):
            try:
                my_id = my_id.strip()
                vdisk = VDiskList.get_vdisk_by_volume_id(my_id)
                msg = "Restarting volume {} {}".format(vdisk.name, my_id)
                print(msg)
                client = vdisk.storagedriver_client
                client.stop_object(str(vdisk.volume_id), False)
                client.restart_object(str(vdisk.volume_id), False)
                j.errorconditionhandler.raiseOperationalWarning(
                    message=msg,
                    category='selfhealing',
                )
            except RuntimeError:
                continue
            except AttributeError:
                continue


if __name__ == '__main__':
    action()
