## GOAL:
Monitor free os diskspace.

## DESCRIPTION:
Free diskspace should always be at least 20% of the capacity of the partition on which the host os is running.   
If it host os has less then 20%, call `logtruncate` JumpScript on self to clean up
**Note:** use internal redis job  
**Note:** This should be part of https://github.com/0-complexity/selfhealing/blob/master/jumpscripts/healthchecks/info_gather_disks.py
