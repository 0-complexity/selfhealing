# JumpScript Categories

## Collectors_reality
Collect info from system & send to grid manager

## Collectors_stats
Collect performance related info & put in redis

## Collectors_controller
Collect info from redis on the controller & send to local influxdb

## Healthchecks
Will do a real time check & if required send alert to grid manager
Result is status page in grid management portal

## Selfhealing
Check against redis & influxdb & if required ask for an action to CB

## Maintenance
E.g. clean logs ...
