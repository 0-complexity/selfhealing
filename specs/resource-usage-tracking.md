> Work in progress specs

# Introduction
This specifications explains how we aggregate `account` consumption over multiple physical locations.
Since a cloudspace is bound to a single physical location `gid`, an account can have multiple spaces over different locations and we 
need to aggregate the account conusmption of resources.

To accomplish this, we need to collect consumption per cloudspace per location (hourly) and push it to a single up stream destination 
(`master`) where we do a final aggregation per `account`.

# Requirements
- Aggregation per location is done hourly on the controller machine (cron: `0 * * * *`)
- Aggregation is done per account, for each our a file is created with the aggregated account data
- Account data is stored as a `capnp` structure (with compression to save space)
- Upstream aggregation is done on the environment `master` (cron: `30 * * * *`) (the 30 min delay to make sure downstream aggregation is complete)
- Aggregation is done per account, for each our a file is created with the aggregated account data (but this case it will contain data from all account spaces)

# Techincal specifications
## Controller aggregation
All controllers now have a js8 with jsagent78 running, this will make it easy to schedule and execute jumpscripts on the controller node.
- A jumpscript should be scheduled (hourly) to do the aggregation per account for this `grid id` (physical location)
- Data collection of the space should be retrieved from influxdb since that is the only location that has historical usage data on the system
 - Query influx to retrieve the last hourly data
 - Jo suggests we retrieve the data directly from redis, but this means that the jumpscript has to find and try get the data from every redis instance on the grid. 

For each cloudspace we need to create the following file
```
$var/resourcetracking/$accountid/$year/$month/$day/$hour.bin
```
Where the data is a `LIST` of capnp structurs defined as following:

```go
struct VM {
  mem
  size
  cpu_minutes
  iops 
  struct Network {
    tx 
    rx
  }
  // extra meta (space id, vm id, etc...)
}
```

The file contains a list of the above structure, the structure has the data per `MACHINE`.

- We need one extra jumpscript on the controller to retrieve capnp files (given account id and time) 

## Master (upstream) aggregation 
The master aggregation script should also run hourly but on the 30's min of the hour, just to give the controllers enough time to do their part

- The master jumpscript will retrieve all the capnp files for the current hour per acocunt id. This can be easily accomplished by calling the jumpscript
to retrieve the files on all controllers.
- Same aggregation process is done and and then rewritten to a file on the master node.

## Utils
We need a simple example script that converts the compressed capnp file into an excel sheet for demonstration.
