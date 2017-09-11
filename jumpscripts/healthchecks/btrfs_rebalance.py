from JumpScale import j

descr = """
Jumpscript to run btrfs balance 
"""

organization = "GIG"
author = "david@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = True
queue = 'process'
roles = []
enable = True
roles = ['cpunode','storagenode','controller']
log = True


def action():
    import os 
    os.system("sudo echo "0 0 */5 * *  /bin/btrfs balance start -dusage=80 /"  | crontab")         

if __name__ == "__main__":
   action()
