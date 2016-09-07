
## GOAL:
Validate all servers are in sync

## DESCRIPTION:

Make sure all serves are in sync
When servers are out of sync more then 10seconds make warning for more then 1minute make error

### question:
@delandtj how to check this?

### Answer

I would say that it's difficult to scheck, but we can rely on the ntp protocol to make sure time on all machine are effectively in sync, without too much worries.

### NTP 

Don't check if time is ok, rather, just set it ok.  
You'll need
  * a working Internet connection (that is checked for already, so we assume it is)
  * a time server (no need to provide one of our own, as we have Internet)
  * initialize time and write that to the computer's clock
  * to setup an ntp daemon
  * (in that order)

### On with it

```
# install necessary packages
apt-get install ntpdate # should be there
# get first time time
# but first stop ntpd (the daemon) if it would be running
service ntpd stop # (or systemctl stop ntpd)
ntpdate pool.ntp.org

# do it again (just to make sure)
ntpdate pool.ntp.org

# Write time to hardware, so that after reboot, there is not too much of an offset
hwclock --systohc

# Start ntpd again
service ntpd start # (or systemctl start ntpd)

```

Conclusion: All that is done @ install of the node,
We can safely rely on the fact that our clocks are properly in sync, no need to check.

Ergo: no checks needed




