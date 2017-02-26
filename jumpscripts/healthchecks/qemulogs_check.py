from JumpScale import j

descr = """
Inspects the qemu log files of running VMs and reports if there was any errors.
"""

organization = 'cloudscalers'
author = "thabeta@codescalers.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['cpunode']
period = 300  # 5 mins
enable = True
async = True
queue = 'process'
log = False


def action():
    from CloudscalerLibcloud.utils.libvirtutil import LibvirtUtil
    from multiprocessing.pool import ThreadPool as Pool

    category = "QEMU Logs"
    vmlogpath = "/var/log/libvirt/qemu/{vm_name}.log"
    libvirt = LibvirtUtil()
    domains_list = [domain['name'] for domain in libvirt.list_domains() if domain['state'] == 1]

    # go for multiprocessing.
    results = []

    def report_domain(domain):
        logpath = vmlogpath.format(vm_name=domain)
        with open(logpath) as f:
            last10 = f.readlines()[-1:-10]
            for line in last10:
                if 'error' in line.lower():
                    results.append(dict(state='ERROR', category=category, message=line))

    pool = Pool(50)
    pool.map(report_domain, domains_list)

    if len(results) == 0:
        results.append(dict(state='OK', category=category, message="QEMU Logs are OK."))

    return results

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))