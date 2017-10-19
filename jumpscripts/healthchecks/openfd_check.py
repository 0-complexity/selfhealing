from JumpScale import j

descr = """
Checks the number of open file descriptors for each process.
Result will be shown in the "System Load" section of the Grid Portal / Status Overview / Node Status page.
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
        try:
            state = None
            soft, hard = proc.rlimit(psutil.RLIMIT_NOFILE)
            count = proc.num_fds()
            if count > 0.8 * soft:
                state = 'WARNING'
            elif count > 0.9 * soft:
                state = 'ERROR'
            if state is not None:
                msg = "Too many open file descriptors for {} with PID {} {}/{}".format(proc.cmdline(), proc.pid, count, soft)
                uid = "{}".format(proc.pid)
                results.append({'state': state, 'message': msg, 'category': category, 'uid': uid})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # process exited just carry on like it never existed
            pass
    if len(results) == 0:
        msg = 'Open file descriptors are all OK'
        results.append({'state': 'OK', 'message': msg, 'category': category})
    return results

if __name__ == '__main__':
    import yaml
    print(yaml.safe_dump(action(), default_flow_style=False))
