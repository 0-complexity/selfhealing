## Policing , aka drop that shizzle

Limiting bandwidth for a vm can only be done properly on egress interfaces, i.e. interfaces of the vm to the host are difficult to shape.
we could set an ingress filter, but that would only be capable to drop packets of which the aggregate bandwidth exceed a certain limit ( 1Mbit for example, could be 5Kpps of small udp frames, or millions of TCP syn packets)
Policing on ingress (that can only drop) needs to be accompanied by an egress shaper too (as we dont know the direction), to limit bandwith TO the vm

Definitions :  
   1) from the host perspective , ingress is traffic coming FROM the vm, egress is traffic going TO the vm.  
   2) A ROS has two interfaces that can be used for policing/shaping  
   3) The vx-00aa vxlan VTEP is, from the host's perspective, an egress port, that can be used to enforce a standard bandwidth limitation.  

Requirements:
We need to know (from influx or any other bw monitor) what the actual bandwidth and pps (packets per second) rate is for the interface that generated the alert.

In a correct situation, we would have  
   1) an alert for vm-${num}-${netidinhex} on a cpu node  
   2) an alert for vx-${netidinhex} on a cpu node hosting the vm  
   3) an alert for vx-${netidinhex} on a cpu node hosting the ROS  
   4) an alert for spc-${netidinhex} on a cpu node hosting the ROS  
   5) an alert for pub-${netidinhex} on a cpu node hosting the ROS  
   6) an alert for vxbackend on all cpu nodes (maybe, depending on the type of attack)  

When a trigger/alert is generated for bw/pps to/from a vm (can as well be a routeros_xxxx), immediate action would be a jumpscript that issues these commands to limit the vm's network usage.
Shaping is not possible, so we police traffic coming from the vm, dropping packets in line with the allowed bandwidth for everyting that is not ssh and/or rdp, so that a user can still access the vm for analysing.

So: FROM the VM

```
# police traffic coming in
iface=vm-3-00c9
prio=100
rate=1mbit
burst=1200kbit
delay=400ms
# Add 2 rules, one to narrow down bw utilisation in any case and one to still allow interactivity for ssh to the vm (we could envision rdp as a third rule)

# first create ingress policer
tc qdisc add dev ${iface} handle ffff: ingress

# allow ssh to continue to work
tc filter add dev ${iface} parent ffff: protocol ip \
    pref ${prio} u32 match ip dport 22 0xffff flowid 1: \
    police rate 100mbit burst 100mbit \
    mpu 0 action continue continue
# same for 3389 (RDP) ?
tc filter add dev ${iface} parent ffff: protocol ip \
    pref ${prio} u32 match ip dport 3389 0xffff flowid 1: \
    police rate 100mbit burst 100mbit \
    mpu 0 action continue continue

# police everything else FROM the VM (really tight, most protocols will stop working)
tc filter add dev ${iface} parent ffff:  u32 \
    match u32 0 0 police rate ${rate} burst ${burst} \
    flowid 1: action drop continue

# Shape traffic outgoing on vxlan vtep
# here we can be a little bit smarter/astuce

# Create Token Bucket Filter
tc qdisc add dev ${iface} root handle 1: prio

# classify traffic
# rate traffic to vm for interactive (22,3389)
tc qdisc add dev ${iface} parent 1:2 handle 20: tbf \
    rate ${rate} buffer 1600 limit 3000
# all the rest sluggish
tc qdisc add dev ${iface} parent 1:3 handle 30: netem \
    delay ${delay}
# set filters
tc filter add dev ${iface} protocol ip parent 1: \
    prio 2 route flowid 1:1
# send dport 22 and 3389 TO vm on the happy path
tc filter add dev ${iface} protocol ip \
    parent 1: prio 1 u32 match ip dport 22 0xffff flowid 1:2
tc filter add dev ${iface} protocol ip \
    parent 1: prio 1 u32 match ip dport 3389 0xffff flowid 1:2
# send all the rest to the delayer
tc filter add dev ${iface} protocol ip \
    parent 1: prio 1 u32 match u32 0 0 flowid 1:3
```

For changing the (already set) limitations in place

```
# Change bandwidth
iface=vm-3-00c9
prio=100
rate=10mbit
burst=11mbit

handle=`tc filter show dev ${iface} parent ffff: | \
    awk -F'fh' '/fh/&&/::/{split($2,a," ");print a[1]}'`

tc qdisc change dev ${iface} parent 1:2 handle 20: tbf \
    rate ${rate} burst ${burst} limit 3000
tc filter change dev ${iface} parent ffff: pref ${prio} \
    handle ${handle} u32 police rate ${rate} burst ${burst}

```

Stop the limiter:

```
# Delete limit
iface=vm-3-00c9

tc qdisc del dev ${iface} root
tc qdisc del dev {iface} parent ffff:
# this removes  all qdiscs, classes and filters for this device
```
