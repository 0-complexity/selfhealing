# Goal:

Make sure all configured raid devices are still healthy

# Description

Check should run every 10 minutes

Validate that cat /proc/mdstat all devices are healthy.
Validate btrfs builtin raid devices if they are configured.


When we can lose a disk and we can still afford to loose another raise a warning
If we can not affort to loose another disk raise error.
