from JumpScale import j
import psutil
import re
import time
import os
import datetime
from collections import defaultdict

descr = """
Find all logs known logs files and executes logs truncate
"""

organization = "0-complexity"
author = "muhamada@greenitglobe.com"
license = "bsd"
version = "1.0"
category = "monitor.maintenance"

async = True
queue = "process"
roles = []
enable = True

log = True
timeout = 60 * 5


class LogArchiver:
    def __init__(self):
        self.client = None
        self.sftp = None
        try:
            from CloudscalerLibcloud.utils.gridconfig import GridConfig

            self.config = GridConfig()
            server = self.config.get("log_server")
            if server:
                import paramiko

                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.WarningPolicy())
                try:
                    self.client.connect(
                        server["host"],
                        server.get("port", 22),
                        server.get("username"),
                        server.get("password"),
                    )
                    self.sftp = self.client.open_sftp()
                except Exception as e:
                    j.errorconditionhandler.processPythonExceptionObject(e)
        except ImportError:
            pass
        self.destfolder = "/".join(
            j.system.net.getHostname().split(".")[::-1]
            + [time.strftime("%Y%m%d-%H%M%S")]
        )

    def make_dirs(self, destfile):
        root = []
        for segment in destfile.split("/")[:-1]:
            root.append(segment)
            self.sftp.mkdir(j.system.fs.joinPaths(*root))

    def archive_log(self, filepath):
        if not self.sftp:
            return
        dest = j.system.fs.joinPaths(self.destfolder, filepath.strip("/"))
        self.make_dirs(dest)
        self.sftp.put(filepath, dest)


def action(locations=["/opt/jumpscale7/var/log/", "/var/log/"], freespace_needed=20.0):
    # mountpoints: List of mountpoints where we can do potential cleaning
    # freespace_needed: Percentage of free diskspace needed at least
    logarchiver = LogArchiver()

    if "/var/log/" not in locations:
        locations.append("/var/log/")

    # Build list of files to truncate
    logfiles = list()
    for location in locations:
        j.system.fswalker.walk(
            location,
            lambda _, path: logfiles.append(path),
            pathRegexIncludes=[".*log.*", ".*\.\d+(\.gz)?$"],
        )

    # Organize logfiles per partition
    partitions = psutil.disk_partitions()
    partitions.sort(key=lambda p: len(p.mountpoint), reverse=True)
    logfiles_per_partition = defaultdict(list)
    for logfile in logfiles:
        logfiles_per_partition[
            next((p for p in partitions if logfile.startswith(p.mountpoint)))
        ].append(logfile)

    # Cleanup logs in each partition
    errors = list()
    for partition, logfiles in logfiles_per_partition.iteritems():
        errors.extend(
            _cleanup_logs_in_partition(
                partition, logfiles, freespace_needed, logarchiver
            )
        )
    # In case any error occurred raise error
    if errors:
        raise RuntimeError("Failures in log cleanup:\n\n{}".format("\n\n".join(errors)))
    for service in j.system.platform.ubuntu.listServices().keys():
        if "nginx" in service:
            j.system.platform.ubuntu.restartService(service)


def _cleanup_logs_in_partition(partition, logfiles, freespace_needed, logarchiver):
    def check_diskspace():
        return 100 - psutil.disk_usage(partition.mountpoint).percent > freespace_needed

    errors = list()

    # Do we need to cleanup stuff uberhaupt ?
    if check_diskspace():
        return errors

    # Stage 1: Delete rotated logfiles
    r = re.compile(".*\.\d+(\.gz)?$")
    for logfile in [lf for lf in logfiles if r.match(lf)]:
        j.logger.log('rm "{}"'.format(logfile), 1)
        try:
            logarchiver.archive_log(logfile)
            j.do.delete(logfile, force=True)
            logfiles.remove(logfile)
        except Exception as e:
            error_message = 'failed to delete "%s": %s' % (logfile, e)
            j.logger.log(error_message, 2)
            errors.append(error_message)

    # Do we need to continue ?
    if check_diskspace():
        return errors

    # Stage 2: Delete other logfiles, start with largest files until enough space is free
    logfiles.sort(key=lambda f: os.stat(f).st_size, reverse=True)
    for logfile in logfiles:
        j.logger.log('truncate "%s"' % logfile, 1)
        try:
            logarchiver.archive_log(logfile)
            with open(logfile, "w") as f:
                f.truncate()  # open in write mode would truncate the file anyway but just to make sure.
                f.write(
                    "Logfile truncated by JumpScale agent on {}\n".format(
                        datetime.datetime.now()
                    )
                )
            if check_diskspace():
                break
        except Exception as e:
            error_message = 'failed to truncate "%s": %s' % (logfile, e)
            j.logger.log(error_message, 2)
            errors.append(error_message)

    if len(logfiles) != 0:
        nid = j.application.whoAmI.nid
        gid = j.application.whoAmI.gid
        j.errorconditionhandler.raiseOperationalWarning(
            message="logfiles truncated on nid:%s gid:%s" % (nid, gid),
            category="selfhealing",
            tags="log.truncate logfiles:%d errors:%d" % (len(logfiles), len(errors)),
        )

    return errors


if __name__ == "__main__":
    action()
