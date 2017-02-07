from JumpScale import j

descr = """
This script make sure any rouge volumedriver is killed by checking its threads count and memory consumption
"""

organization = "greenitglobe"
author = "muhamada@greenitglobe.com"
category = "monitor.maintenance"
license = "bsd"
version = "1.0"
order = 1
enable = True
async = True
log = False
queue = 'process'
roles = ['storagedriver']


def action(vpool):
    import psutil
    for process in psutil.process_iter():
        if process.name() != 'volumedriver_fs':
            continue

        cmd = ' '.join(process.cmdline())
        if '--mountpoint /mnt/{}'.format(vpool) not in cmd:
            continue

        # we found which volumedriver_fs
        return process.memory_percent()

    return None


if __name__ == '__main__':
    print(action('vmstor'))
