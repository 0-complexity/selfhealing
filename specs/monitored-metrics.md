# Summary

- Disk
    - disk.iops.read [#] [PHYS,VIRT]
    - disk.iops.write [#] [PHYS,VIRT]
    - disk.throughput.read [MB] [PHYS,VIRT]
    - disk.throughput.write [MB] [PHYS,VIRT]
    - disk.temperature [°C] [PHYS]
- Network
    - network.packets.rx [#] [PHYS,VIRT]
    - network.packets.tx [#] [PHYS,VIRT]
    - network.throughput.incoming [MB] [PHYS,VIRT]
    - network.throughput.outgoing [MB] [PHYS,VIRT]
- CPU
    - machine.CPU.utilisation [s] [PHYS,VIRT]
    - machine.CPU.percent [%] [PHYS]
    - machine.CPU.temperature [°C] [PHYS]
- Host machine
    - machine.memory.ram.available [MB] [PHYS]
    - machine.memory.swap.left [MB] [PHYS]
    - machine.memory.swap.used [MB] [PHYS]
    - machine.CPU.contextswitch [#] [PHYS]
    - machine.CPU.interrupts [#] [PHYS]
    - machine.CPU.interrupts [#] [PHYS]
    - machine.temperature [°C] [PHYS]

# Disk

- disk.iops.read [#] [PHYS,VIRT]
- disk.iops.write [#] [PHYS,VIRT]
- disk.throughput.read [MB] [PHYS,VIRT]
- disk.throughput.write [MB] [PHYS,VIRT]
- disk.temperature [°C] [PHYS]

Use smartctl -A /dev/sda | awk '/Temp/{print $10}', make sure smartmontools are installed

## Notation

For physical machines we will be using the gid/nid combination to identify the machine and the device name to identify the monitored device.

For virtual machines we will be using the vdiskid from the model. The metric collection jumpscript on the physical node will do the matching between the model and the deployed vdisks and cache the result into the local redis to not overload the model server.

- physical: disk.iops.read@phys.[gid].[nid].[device_name]
- virtual: disk.iops.read@virt.[vdiskid]
- example:
  - disk.iops.read@phys.2.3.sda = 238
  - disk.iops.read@virt.45 = 2568

The metrics for iops as wel as for throughput will always be growing, so we'll have to write the logic ourselves to transform them into activity over the last x seconds. This should normally be taken care of by the lua scripts in the redis key value store.

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

- network.packets.rx [#] [PHYS,VIRT]
- network.packets.tx [#] [PHYS,VIRT]
- network.throughput.incoming [MB] [PHYS,VIRT]
- network.throughput.outgoing [MB] [PHYS,VIRT]

## Notation

For physical machines we will be using the gid/nid combination to identify the machine and the device name to identify the monitored device.

For virtual machines we will be using the macaddress which allows to easily look it up in the model afterwards

- physical: network.packets.rx@phys.[gid].[nid].[device_name]
- virtual: network.packets.rx@virt.[macaddress]
example:
- network.packets.rx@phys.2.3.eth0 = 238
- network.packets.rx@virt.45 = 2568

Metrics of Network will also be ever growing, so the same comment applies on Network like on Disk.

### Implementation hints

```
cat /sys/class/net/vm-138-00d5/statistics/rx_packets
8769876987
```

# Memory

We only monitor memory of the physical machine.

The following are important:

- machine.memory.ram.available [MB] [PHYS]
- machine.memory.swap.left [MB] [PHYS]
- machine.memory.swap.used [MB] [PHYS]

## Notation

For physical machines we will be using the gid/nid combination to identify the machine.

- physical: machine.memory.ram.available@phys.[gid].[nid]
example:
- machine.memory.ram.available@phys.2.3 = 238

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

- machine.CPU.contextswitch [#] [PHYS]
- machine.CPU.utilisation [s] [PHYS,VIRT]
- machine.CPU.interrupts [#] [PHYS]
- machine.CPU.percent [%] [PHYS]
- machine.CPU.temperature [%] [PHYS]

## Notation

For physical machines we will be using the gid/nid combination to identify the machine and the cpu number to identify the monitored device.

For virtual machines we will be using the vmid from the model which allows to easily look it up in the model afterwards.

- physical:
  - machine.CPU.contextswitch@phys.[gid].[nid]
  - machine.CPU.utilisation@phys.[gid].[nid].[cpu-number]
  - machine.CPU.percent@phys.[gid].[nid].[cpu-number]
  - machine.CPU.temperature@phys.[gid].[nid].[cpu-number]
  - machine.CPU.utilisation@virt.[vmid]
example:
- machine.CPU.contextswitch@phys.2.3 = 238

## Tags
- Add tags for temp\d_label and location under hwmon


### Implementation hints 4 contextswitch & interrupts

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

### Implementation hints 4 temperature of cpus
Collect data system temperature from `/sys/class/hwmon/*/temp*_{input,value}`


### Implementation hints 4 utilisation on virtual machines

```
root@cpu-01:~# virsh dominfo 6
Id:             6
Name:           vm-1
UUID:           eab0aa16-8faf-46b5-a85a-d5da8e5132a8
OS Type:        hvm
State:          running
CPU(s):         1
CPU time:       3381.0s
Max memory:     1000448 KiB
Used memory:    1000000 KiB
Persistent:     yes
Autostart:      disable
Managed save:   no
Security model: none
Security DOI:   0
```

# System Temperature

- machine.temperature [°C] [PHYS]
