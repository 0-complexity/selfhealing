from JumpScale import j

descr = """
Get OVS packages.
"""

organization = "cloudscalers"
author = "khamisr@codescalers.com"
version = "1.0"
roles = ["storagedriver"]
enable = True
async = True
queue = "process"
log = True


def action():
    ovsresults = {}
    for package in j.system.platform.ubuntu.getInstalledPackages():
        if "alba" in package.name or "openvstorage" in package.name:
            ovsresults[package.name] = package.version

    return ovsresults


if __name__ == "__main__":
    print action()
