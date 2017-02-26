## Network load generated by vms

### What needs to be shaped (or policed) and how

Network shaping is a difficult thingie to do correctly, as (most) traffic can be considered necessary and keeping customers networks down makes for a lesser user experience.
But even then, we should be aware that any vm can become rogue and start generating attack packets going out to some poor bloke that needs killing for some reason. Last time I checked on an issue in be-scale1, the bloke was a chinese who must've been serioulsly punked.  
The compromised and attacking VM was generating almost 400Kpps of 250 length, sending them over the vxlan , through the ROS, out onto the Public VLAN, (all gigabit) to the Telenet public port that is 100MBit.
Needless to say, not much traffic could be handled in such a storm, even our poor old core router (Cisco 3560 from around 2005) was barely responsive.

Traffic coming OUT of a VM, meaning that from the hypervisor's point of view this traffic is INCOMING, is essentially A DoS attack. Packets arrive from the VM at a certain rate, and we can only limit the number of packets that get forwarded by the virtual switch.

So for us, we need to handle essentially a DoS, or even a limited form of DDos (2 or more vms in the same CloudSpace on the same hypervisor).

There are not many tools to do that, as the tap device from the VM itself just forwards, and there are no packet shapers IN the tap, there are only shapers for NICs. And the latest non-blocking and zero-copy tap devices can easily handle 10+GBit/sec on an old Core i7 first gen.

## Applying to our setup

## OVS (openvswitch)

OVS has a hook to limit ingress which is basically just drop packets when bandwidth reaches a certain limit (don't understand that there is no way to counter packets/sec). This is called 'Policing', opposed to 'Shaping' when you want to properly put packets in queues and let them trickle out in a controlled way.

Hence brute-force policing is only available on incoming (coming out of the vm), whereas shaping can be done for packets going out on the vxlan.

For now, absent a proper daemon that keeps accounting in memory per vm and reacts a lot more efficiently, we'll 'just' police ingress, using the data from infux and act with selfhealing.  
That means that our reaction time over 2 iterations of 5 min and another to shut down the VM will be 15 min. Can we live with that ?

Most of the time, rogue VMs that partake in a DoS will send at highest pace available crafted packets (tcp and/or udp) to one or more hosts.  

So if PPS = warning/error (need to decide)
  - is ROS *ALSO* sending the (roughly) same amount of packets?
    - YES
	  - limit packets TO ROS (we want to limit packets TO ROS, as it might be possible that other VMS's from ths cloudspace are also compromised)
	  - limit packets FROM VM (Policing = DROP everything that doesn't fit)
	- NO
	  - So this is probably inter-VM traffic -> do we want to limit that ? if so : limit traffic on Tenants VTEP (vx-aaaa) too
	  This is probably a good idea, as we found one problematic vm, others could be compromised too...

### Rules to insert

#### Ingress Policing: limit vm outgoing traffic

#### Possibility 1 (inefficient and difficult to limit, as packets get dropped, and it's impossible to shape in any way) *don't use the OVS provided soluton, as it's too limited*

  - for coming in from VM, the OVS hooks are harsh and injust :-)

  ```
  ovs-vsctl set Interface vm-4243-00dc ingress_policing_rate=100000 # 100.000 KBit = 100Mbit
  ovs-vsctl set Interface vm-4243-00dc ingress_policing_burst=80000 # to have TCP still working  (80%)
  ```

  You can verify proper inserts with

  ```
  tc -s qdisc show dev vm-4243-00dc
  tc -s filter show dev vm-4243-00dc parent ffff:
  ```

  - remove the rules with

  ```
  ovs-vsctl set Interface vm-4243-00dc ingress_policing_rate=0
  ```

#### Possibility 2 (better, but needs an intermediate device to handle queues)

By using the kernel's `ifb` device, we can send all packets coming in from a VM to an interface that actually can do some hierarchical bandwidth limiting, making sure that rates are enforced.
The ifb can get all traffic redirected and all packets coming out from the ifb are effectively OUT packets, so can be SHAPED

To get the rate at which we want to shape the VM's interface we need to get an idea of what type of packets are in flight.  
Size matters, as the actual bandwidth is `pps * avg packet size`.  
Therefore, if we want to shape , we calculate the average packet size and that needs to fit in the shaping allowed bandwidth.  
Advantage is that we can then add some latency to these flows so that the rate at which packets get sent out, are reduced to a minimal

So:

We know last 5 min pps (LASTPPS)

We know last 5 min BW (LASTBW)

We want to get the output rate to 10K pps

Hence : ( all calc is bytes/sec, recalculate your measurements )

```
AVGPKT = LASTBW / LASTPPS
NEWBW  = 10000 * AVGPKT
```

That basically means that if the average pkt size was 200bytes, the new rate would be 2000000 bytes/sec .  

effectively 2000000 * 8 = 16mbit or 16000kbit

if after 5 minutes the bandwidth is *still* 16mbit, limit furter to 1/4th of previous, i.e. 4000kbit and double the latency for good measure  
and after another 5 min ... still 4000kbit , the we can probable safely envision shutdown of the vm  

like so :

```
#!/bin/bash
VMIF=vm-4519-00df
IFB=ifb-00df
TXQ=8
RATE=10mbit  
BURST=1mbit
DELAY=200ms

function start(){
	# create mq IFB for  
	modprobe ifb numifbs=0 2> /dev/null
	ip link add $IFB numtxqueues $TXQ type ifb 2> /dev/null
	ip l set $IFB up

	# redirect all traffic coming IN from VM to ifb
	tc qdisc del dev $VMIF ingress
	# replace libvirt iptables mark based ingress filter (will be restored when vm gets restarted)
	tc filter del dev $VMIF parent 1: pref 1
	tc qdisc add dev $VMIF ingress
	tc filter add dev $VMIF parent ffff: pref 100 protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev $IFB

	# add multiqueue root qdisc to ifb
	tc qdisc del dev $IFB root 2> /dev/null
	tc qdisc add dev $IFB root handle 1: mq
	# and split traffic in multiple queues to be handled as netem leafs
	for i in `seq 1 $TXQ` ; do
		QUEUE=`printf %x $(( $i ))`
		tc qdisc add dev $IFB handle 1:${QUEUE} est 1sec 4sec netem delay $DELAY rate $RATE
		tc qdisc add dev $IFB parent 1:${QUEUE} handle 2:${QUEUE} tbf rate $RATE burst $BURST latency $DELAY peakrate $RATE minburst 1520
	done

	# libvirt added a few qdiscs already (if rate is defined in xml), so we'll
	# need to replace it for traffic going to the VM

	# remove root qdiscs (libvirt ones) from $VMIF
	tc qdisc del dev $VMIF root
	# add the same netem qdisc
	tc qdisc add dev $VMIF root netem $DELAY rate $RATE


}



function stop(){
	tc filter del dev $VMIF parent ffff: prio 1 protocol ip pref 100 u32
	tc qdisc  del dev $VMIF ingress
	ip link delete $IFB
}
```

## Secure Public port of routerOS

A user could be capable of using the GUI of the routerOS to
  - run a dhcp server on the public net (which we definitely do not want)
  - add an ip address to the public interface, of which we don't know the existence
  - advertise an IPv6 subnet
  - run a Prefix delegation server
  - provide dhcpv6

To mi


```

#!/bin/bash
mac=`virsh domiflist 38 | awk '/pub-/{print $5}'`
port=`ovs-vsctl -f table -d bare --no-heading -- --columns=ofport list Interface pub-00df`

# mac="52:54:00:8a:06:3c"
# port=6     
publicipv4subnet=10.101.0.0/16
publicipv4addr=10.101.110.38
function start(){
	ovs-ofctl del-flows public "in_port=${port}"
	cat << EOF > publicrouter.of
# Allow dhcp client
in_port=${port},priority=8000,dl_type=0x0800,nw_proto=0x11,tp_dst=67,dl_src=${mac},idle_timeout=0,action=normal
# Allow arp req
in_port=${port},priority=7000,dl_type=0x0806,dl_src=${mac},arp_sha=${mac},nw_src=0.0.0.0,idle_timeout=0,action=normal
# Drop DHCP server replies coming from here (rogue dhcp server)
in_port=${port},priority=8000,dl_type=0x0800,nw_proto=0x11,tp_src=68,dl_src=${mac},idle_timeout=0,action=drop
# Allow ARP responses.
in_port=${port},priority=7000,dl_type=0x0806,dl_src=${mac},arp_sha=${mac},nw_src=${publicipv4addr}/32,idle_timeout=0,action=normal
# Allow ipv4/mac (note: this is a /32) there can be only one (sic McLeod)
in_port=${port},priority=6000,dl_type=0x0800,dl_src=${mac},nw_src=${publicipv4addr}/32,idle_timeout=0,action=normal
# # For Ipv6 we'll allow from the assigned subnet, but restrictive
# # Who'ze my Neighbour
# in_port=${port},priority=8000,dl_src=${mac},icmp6,ipv6_src={{ipv6prefix}}/64,icmp_type=135,nd_sll=${mac},idle_timeout=0,action=normal
# # I am Neighbour
# in_port=${port},priority=8000,dl_src=${mac},icmp6,ipv6_src={{ipv6prefix}}/64,icmp_type=136,nd_target={{ipv6prefix}}/64,idle_timeout=0,action=normal
# # Standard ipv6 traffic (they can add 2^64 addresses to the pub iface, we don't care)
# in_port=${port},priority=5000,dl_src=${mac},ipv6_src={{ipv6prefix}}/64,icmp6,action=normal
# in_port=${port},priority=5000,dl_src=${mac},ipv6_src={{ipv6prefix}}/64,tcp6,action=normal
# in_port=${port},priority=5000,dl_src=${mac},ipv6_src={{ipv6prefix}}/64,udp6,action=normal
# Drop all other neighbour discovery.
in_port=${port},priority=7000,icmp6,icmp_type=135,action=drop
in_port=${port},priority=7000,icmp6,icmp_type=136,action=drop
# Drop other specific ICMPv6 types.
# Router advertisement.
in_port=${port},priority=6000,icmp6,icmp_type=134,action=drop
# Redirect gateway.
in_port=${port},priority=6000,icmp6,icmp_type=137,action=drop
# Mobile prefix solicitation.
in_port=${port},priority=6000,icmp6,icmp_type=146,action=drop
# Mobile prefix advertisement.
in_port=${port},priority=6000,icmp6,icmp_type=147,action=drop
# Multicast router advertisement.
in_port=${port},priority=6000,icmp6,icmp_type=151,action=drop
# Multicast router solicitation.
in_port=${port},priority=6000,icmp6,icmp_type=152,action=drop
# Multicast router termination.
in_port=${port},priority=6000,icmp6,icmp_type=153,action=drop
# Fsck all the rest
in_port=${port},priority=100,action=drop
EOF
	ovs-ofctl add-flows public publicrouter.of
}
function stop(){
	ovs-ofctl del-flows public "in_port=${port}"
}

case $1 in
	start)
		start
		;;
	stop)
		stop
		;;
	*)
		echo "$0 [stop/start]"
		;;
esac
```

## For blocking the gwm-xxx port on the ROS into the envision

With ROS having a leg into the environment throug it's interface on gw_mgmt, we need to stop any attempt from someone connected on cli of the ROS to access the IP addrs (all cpu nodes) in 10.199.0.0/22

Let's block it off, but allow for the gw_mgmt net to get INTO the ROS

```bash
ros=routeros_00da
bridge=gw_mgmt
rosmac=`virsh domiflist routeros_00da | awk '/gwm-/{print $5}'`
rosport=`ovs-vsctl -f table -d bare --no-heading -- --columns=ofport list Interface pub-${ros/routeros_}`
rosport=$(( $rosport ))
patchport=$(( $patchport ))

# first, remove all forwarding on this bridge
sudo ovs-ofctl del-flows ${bridge}

# drop network chatter
sudo ovs-ofctl add-flow ${bridge} "table=0,priority=100,dl_src=01:00:00:00:00:00/01:00:00:00:00:00, actions=drop"

# drop all UDP
sudo ovs-ofctl add-flow ${bridge} "table=0,priority=100,dl_type=0x0800,nw_proto=17,actions=drop"

# drop all ipv6
sudo ovs-ofctl add-flow ${bridge} "table=0,in_port=${rosport},priority=100,dl_src=${rosmac},dl_type=0x86dd,actions=drop"

# send rest in table 1
sudo ovs-ofctl add-flow ${bridge} "table=0, priority=0, actions=resubmit(,1)"

# Table 1 ; stateful packet filter ( ovs >= 2.5 )

sudo ovs-ofctl add-flows ${bridge} - << EOF
# start dropping it all (fallthrough (lowest priority))
table=1,priority=1,action=drop
# allow all arp (for now)
table=1,priority=10,arp,action=normal
# when an ip packet arrives and is not tracked, send it to the conntracker and continue table2
table=1,priority=100,ip,ct_state=-trk,action=ct(table=2)
# a packet from 10... with dest MAC, that is IP, and is a NEW session packet, commit it in conntracker
table=2,nw_src=10.199.0.0/22,dl_dst=${rosmac},ip,ct_state=+trk+new,action=ct(commit),normal
# and do normal packet forwarding processing on it
table=2,nw_src=10.199.0.0/22,dl_dst=${rosmac},ip,ct_state=+trk+est,action=normal
# otherwise, all new IP sessions get dropped
table=2,in_port=${rosport},ip,ct_state=+trk+new,action=drop
# unless they are related to a comitted session
table=2,in_port=${rosport},ip,ct_state=+trk+est,action=normal
# fall through over prio 10 and 1 (specified above)
EOF

```

TODO : also block arp who-has requests that are NOT specifically for