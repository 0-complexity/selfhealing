## GOAL:
Monitor temperature of hardware of the node

## DESCRIPTION:

### Datacollection

Collect data system temperature from /sys/class/hwmon
For cpu core:
- Store under `machine.CPU.temprature@phys.%d.%d.%d' % (j.application.whoAmI.gid, j.application.whoAmI.nid, cpu_nr)`
- Add tags for cpunr and location under hwmon

For system temperature:
- Store under `machine.temperature@phys.%d.%d % (j.application.whoAmI.gid, j.application.whoAmI.nid)`
- Add tags for temp\d_label and location under hwmon

For disk temperate:
Use smartctl -A /dev/sda | awk '/Temp/{print $10}', make sure smartmontools are installed

-Store under `disk.temperate@phys.<gid>.<nid>.<devicename>`

### Healthcheck:

Compare 5min avg with temp\d_crit if it has reached 90% of crit raise warning of it reached 100% or more raise error

For disks a warning shoudl be raised when temperature is above 50degrees and an error when above 60degrees
