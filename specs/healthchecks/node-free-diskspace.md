## GOAL:
Monitor free os diskspace.

## DESCRIPTION:
Free diskspace should always be at least 20% of the capacity of the partition on which the host os is running. If it host os has less then 20%:
- Truncate log files in:
  - /var/log
  - /optvar/log/
- Report an error to the healthcheck to show that an unusual situation occurred and that we need to check why this happened. Off course also report which files were truncated.

**Remark**: The system should truncate the biggest logfiles first.
