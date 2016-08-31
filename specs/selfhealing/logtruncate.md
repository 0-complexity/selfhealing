
- Truncate log files in:
  - /var/log
  - /optvar/log/
  - /opt/jumpscale7/var/log
- Report an error to the healthcheck to show that an unusual situation occurred and that we need to check why this happened. Off course also report which files were truncated.

**Remark**: The system should truncate the biggest logfiles first.
