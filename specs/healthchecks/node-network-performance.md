## GOAL:
Monitor the speed of the network

## DESCRIPTION:

### Speed :

In essence, speed is derived from the effective detected NIC speed, no need to test haow fast an os can handle ths speed, as the fasteser the NIC is (i.e. 40G) it would be difficult to fill it with a single-threaded app.

[So speed is detected here](https://github.com/0-complexity/selfhealing/blob/master/jumpscripts/healthchecks/networkperformance.py#L58)

### reliability :

We want to measure reliability of a link, sending a bunch of packets, making sure they all reach destination.

Enter iperf3, that can send x udp frames to a server and verify if they're all received.

```
# iperf server:
iperf3 -s
```

```
# iperf3 client where:
#  * bw limit 100Mbit
#  * numpackets +- 1000
iperf3 -c 10.101.106.254 -u -k 1000 -b 100M

Connecting to host 10.101.106.254, port 5201
[  4 ] local 192.168.16.240 port 48300 connected to 10.101.106.254 port 5201
[ ID ] Interval           Transfer     Bandwidth       Total Datagrams
[  4 ]   0.00-0.70   sec  7.81 MBytes  93.1 Mbits/sec  1000  
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID ] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4 ]   0.00-0.70   sec  7.81 MBytes  93.1 Mbits/sec  0.081 ms  0/993 (0%)  
[  4 ] Sent 993 datagrams

```

The iperf client sent here 993 packets of which 0% is lost (got acks for every packet)

```
# set some packet loss engine on nic
tc qdisc add dev backplane1 root netem loss random 10
# Cool uh ?
```

Do it again

```
iperf3 -c 10.101.106.254 -u -k 1000 -b 100M
Connecting to host 10.101.106.254, port 5201
[  4 ] local 192.168.16.240 port 35249 connected to 10.101.106.254 port 5201
[ ID ] Interval           Transfer     Bandwidth       Total Datagrams
[  4 ]   0.00-0.70   sec  7.81 MBytes  93.2 Mbits/sec  1000  
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID ] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4 ]   0.00-0.70   sec  7.81 MBytes  93.2 Mbits/sec  0.093 ms  102/996 (10%)  
[  4 ] Sent 996 datagrams

```

After this test, one can see 10% packets lost

###  Alerts

  * WARNING when 2% packet loss
  * ALERT when 5% packet loss

### iperf3 :

Iperf3 can generate json with a swath of info; what you want :

`end->sum->lost_percent`


```
iperf3 -c 10.101.106.254 --format m -u -k 10000 -b 1000M -J
{
	"start":	{
		"connected":	[{
				"socket":	4,
				"local_host":	"192.168.16.240",
				"local_port":	60667,
				"remote_host":	"10.101.106.254",
				"remote_port":	5201
			}],
		"version":	"iperf 3.1.3",
		"system_info":	"Linux delandtj-Desktop 4.7.2-1-ARCH #1 SMP PREEMPT Sat Aug 20 23:02:56 CEST 2016 x86_64",
		"timestamp":	{
			"time":	"Tue, 06 Sep 2016 11:45:58 GMT",
			"timesecs":	1473162358
		},
		"connecting_to":	{
			"host":	"10.101.106.254",
			"port":	5201
		},
		"cookie":	"delandtj-Desktop.1473162358.163449.3",
		"test_start":	{
			"protocol":	"UDP",
			"num_streams":	1,
			"blksize":	8192,
			"omit":	0,
			"duration":	0,
			"bytes":	0,
			"blocks":	10000,
			"reverse":	0
		}
	},
	"intervals":	[{
			"streams":	[{
					"socket":	4,
					"start":	0,
					"end":	0.785134,
					"seconds":	0.785134,
					"bytes":	81920000,
					"bits_per_second":	834711189.017002,
					"packets":	10000,
					"omitted":	false
				}],
			"sum":	{
				"start":	0,
				"end":	0.785134,
				"seconds":	0.785134,
				"bytes":	81920000,
				"bits_per_second":	834711189.017002,
				"packets":	10000,
				"omitted":	false
			}
		}],
	"end":	{
		"streams":	[{
				"udp":	{
					"socket":	4,
					"start":	0,
					"end":	0.785134,
					"seconds":	0.785134,
					"bytes":	81920000,
					"bits_per_second":	834711189.017002,
					"jitter_ms":	0.092000,
					"lost_packets":	69,
					"packets":	9996,
					"lost_percent":	0.690276,
					"out_of_order":	0
				}
			}],
		"sum":	{
			"start":	0,
			"end":	0.785134,
			"seconds":	0.785134,
			"bytes":	81920000,
			"bits_per_second":	834711189.017002,
			"jitter_ms":	0.092000,
			"lost_packets":	69,
			"packets":	9996,
			"lost_percent":	0.690276
		},
		"cpu_utilization_percent":	{
			"host_total":	17.769540,
			"host_user":	1.931197,
			"host_system":	15.836373,
			"remote_total":	0.136453,
			"remote_user":	0,
			"remote_system":	0.133847
		}
	}
}

```

