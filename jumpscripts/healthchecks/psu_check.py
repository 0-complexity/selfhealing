from JumpScale import j
descr = """

"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60 # 1min
enable = True
async = True
queue = 'process'
log = True

def action():
    results = []
    return results


if __name__ == '__main__':
    print action()
