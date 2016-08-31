## GOAL:
Monitor fans of the physical nodes.

## DESCRIPTION:
Using ipmitool we need to monitor the fans of the physical nodes and raise a health check error if a fan stops functioning.

The following shows how you can use ipmitool to read if fans are still functioning correctly. I the 4th column show **'ok'** then all is ok.
```
root@cpu-04:~# ipmitool sensor | grep '^FAN.*'
FAN1             | 8700.000   | RPM        | ok    | 300.000   | 500.000   | 700.000   | 25300.000 | 25400.000 | 25500.000
FAN2             | 5200.000   | RPM        | ok    | 300.000   | 500.000   | 700.000   | 25300.000 | 25400.000 | 25500.000
FAN3             | 8900.000   | RPM        | ok    | 300.000   | 500.000   | 700.000   | 25300.000 | 25400.000 | 25500.000
```

When we manually blocked the fan with Jans finger we saw that the status of the sensor reported **'nr'** indicating there was a problem. Probably there are more error statusses, so as soon as the status is **NOT 'ok'**, we should report an error to the healthcheck.
```
root@cpu-04:~# ipmitool sensor | grep '^FAN.*'
FAN1             | 8700.000   | RPM        | ok    | 300.000   | 500.000   | 700.000   | 25300.000 | 25400.000 | 25500.000
FAN2             | na         | RPM        | nr    | 300.000   | 500.000   | 700.000   | 25300.000 | 25400.000 | 25500.000
FAN3             | 8900.000   | RPM        | ok    | 300.000   | 500.000   | 700.000   | 25300.000 | 25400.000 | 25500.000
```
