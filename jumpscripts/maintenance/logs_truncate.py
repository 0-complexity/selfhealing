from JumpScale import j

descr = """
Find all logs known logs files and executes logs truncate
"""

organization = "0-complexity"
author = "muhamada@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitor.maintenance"

async = True
queue = 'process'
roles = []
enable = True

log = True

def action(mountpoint='/opt/'):
    def callback(_, file):
        j.logger.log('truncate "%s"' % file, 1)
        try:
            with open(file, 'w') as f:
                f.truncate() # open in write mode would truncate the file anyway but just to make sure.
        except Exception as e:
            j.logger.log('failed to truncate "%s": %s' % (file, e), 2)

    j.system.fswalker.walk(mountpoint, callback, pathRegexIncludes=['.*\.log$'])

if __name__ == '__main__':
    action('/opt/jumpscale7/')
