## GOAL:
Monitor temperature of hardware of the node

### Healthcheck:

Compare 5min avg with temp\d_crit if it has reached 90% of crit raise warning of it reached 100% or more raise error

For disks a warning shoudl be raised when temperature is above 60degrees and an error when above 70degrees
