# Summary

- Disk
    - Disk.iops.read [#] [PHYS,VIRT]
    - Disk.iops.write [#] [PHYS,VIRT]
    - Disk.throughput.read [MB] [PHYS,VIRT]
    - Disk.throughput.write [MB] [PHYS,VIRT]
- Network
    - Network.packets.rx [#] [PHYS,VIRT]
    - Network.packets.tx [#] [PHYS,VIRT]
    - Network.throughput.incoming [MB] [PHYS,VIRT]
    - Network.throughput.outgoing [MB] [PHYS,VIRT]
- Host machine
    - Machine.memory.ram.available [MB] [PHYS]
    - Machine.memory.swap.left [MB] [PHYS]
    - Machine.memory.swap.used [MB] [PHYS]
    - Machine.CPU.contextswitch [#] [PHYS]

# Disk

## Load

- Disk.iops.read [#] [PHYS,VIRT]
- Disk.iops.write [#] [PHYS,VIRT]
- Disk.throughput.read [MB] [PHYS,VIRT]
- Disk.throughput.write [MB] [PHYS,VIRT]

The metrics that will be reading for iops as wel as for throughput will always be growing, so we'll have to write the logic ourselves to transform them into activity over the last x seconds. This should normally be taken care of by the lua scripts in the redis key value store.

### Implementation hints on Physical machines

/proc/diskstats

More information on /proc/diskstats can be found here: https://www.kernel.org/doc/Documentation/ABI/testing/procfs-diskstats

```
root@jabber-europe-01:~# cat /proc/diskstats
   1       0 ram0 0 0 0 0 0 0 0 0 0 0 0
   1       1 ram1 0 0 0 0 0 0 0 0 0 0 0
...
   7       6 loop6 0 0 0 0 0 0 0 0 0 0 0
   7       7 loop7 0 0 0 0 0 0 0 0 0 0 0
   8       0 sda 72304106 4677305 9050957276 1331648972 363862326 236544654 3706879688 3352669632 0 2086758420 389941568
   8       1 sda1 71342551 4568658 9042395616 1311756012 223365180 235833140 3700227680 1402484004 0 1164062620 2714904312
   8       2 sda2 2 0 4 52 0 0 0 0 0 52 52
   8       5 sda5 961508 108619 8561072 19892660 119981 711514 6652008 2450452 0 4537720 22343256
   8      16 sdb 71338120 4613418 9042767942 300481632 363748154 235827764 3700227680 3266247832 0 2002954636 3567389740
   8      17 sdb1 71337980 4613359 9042766362 300478788 223370989 235827764 3700227680 1381443992 0 1126937392 1682621556
   8      18 sdb2 2 0 4 0 0 0 0 0 0 0 0
   8      21 sdb5 93 31 992 1728 0 0 0 0 0 1724 1728
   9       0 md0 11489396 0 116849762 0 544743328 0 3261302936 0 0 0 0
 252       0 dm-0 429553 0 28370842 1839184 63485938 0 534246264 500950836 0 429919516 502814728
 252       1 dm-1 1385433 0 11083464 12662272 385096613 0 2202447016 3353272768 0
 ...
 ```

### Implementation hints on Virtual machines

We can connect to libvirt from python as shown below:

```
In [43]: con = libvirt.open()

In [44]: vm = con.listAllDomains()[1]

In [45]: vm.blockStats('/mnt/vmstor/vm-12/base_image.raw')
Out[45]: (596986L, 2453889024L, 5125L, 2538033152L, 18446744073709551615L)
```

# Network

- Network.packets.rx [#] [PHYS,VIRT]
- Network.packets.tx [#] [PHYS,VIRT]
- Network.throughput.incoming [MB] [PHYS,VIRT]
- Network.throughput.outgoing [MB] [PHYS,VIRT]


Metrics of Network will also be ever growing, so the same comment applies on Network like on Disk.

### Implementation hints

```
cat /sys/class/net/vm-138-00d5/statistics/rx_packets
8769876987
```

# Memory

We only monitor memory of the physical machine.

The following are important:

- Machine.memory.ram.available [MB] [PHYS]
- Machine.memory.swap.left [MB] [PHYS]
- Machine.memory.swap.used [MB] [PHYS]

### Implementation hints

```
cat /proc/meminfo
root@fastgeert-VirtualBox:~# cat /proc/meminfo
...
MemAvailable:    1821220 kB
...
SwapTotal:       4092924 kB
SwapFree:        4092924 kB
...
```

# CPU

- Machine.CPU.contextswitch [#] [PHYS]

### Implementation hints

See http://www.linuxhowtos.org/System/procstat.htm

```
> cat /proc/stat
cpu  2255 34 2290 22625563 6290 127 456
cpu0 1132 34 1441 11311718 3675 127 438
cpu1 1123 0 849 11313845 2614 0 18
intr 114930548 113199788 3 0 5 263 0 4 [... lots more numbers ...]
ctxt 1990473
btime 1062191376
processes 2915
procs_running 1
procs_blocked 0
```
