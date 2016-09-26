from JumpScale import j

descr = """
Check on open filescriptors
"""

organization = 'greenitglobe'
author = "deboeckj@greenitglobe.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['node']
period = 60  # 1min
enable = True
async = True
queue = 'process'
log = True


def action():
    import psutil
    category = "System Load"
    results = []

    for proc in psutil.get_process_list():
        state = None
        soft, hard = proc.rlimit(psutil.RLIMIT_NOFILE)
        count = proc.num_fds()
        if count > 0.8 * soft:
            state = 'WARNING'
        elif count > 0.9 * soft:
            state = 'ERROR'
        if state is not None:
            msg = "To many open file descriptors for {} with PID {} {}/{}".format(proc.cmdline(), proc.pid, count, soft)
            results.append({'state': state, 'msg': msg, 'category': category, 'uid': msg})
    if len(results) == 0:
        msg = 'Open filedescriptors are all OK'
        results.append({'state': 'OK', 'msg': 'msg', 'category': category})
    return results

if __name__ == '__main__':
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
