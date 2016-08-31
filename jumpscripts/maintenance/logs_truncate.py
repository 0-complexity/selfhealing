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
        code, _ = j.system.prcess.execute('truncate -s 0 %s' % file, dieOnNonZeroExitCode=False)
        if code != 0:
            j.logger.log('failed to truncate "%s"' % file, 2)

    j.system.fswalker.walk(mountpoint, callback, pathRegexIncludes=['.*\.log$'])
