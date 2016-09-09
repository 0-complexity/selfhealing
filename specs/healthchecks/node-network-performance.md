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
iperf3 -c 10.101.106.254 -k 10000 -b 1G

root@cpu-01:~# iperf3 -c 10.106.1.34 -k 10000 -b 1G 
Connecting to host 10.106.1.34, port 5201
[  4] local 10.106.1.11 port 56216 connected to 10.106.1.34 port 5201
[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd
[  4]   0.00-1.00   sec   109 MBytes   914 Mbits/sec    0    535 KBytes       
[  4]   1.00-2.00   sec   119 MBytes  1.00 Gbits/sec    0   1.04 MBytes       
[  4]   2.00-3.00   sec   119 MBytes  1.00 Gbits/sec    0   1.84 MBytes       
[  4]   3.00-4.00   sec   118 MBytes   994 Mbits/sec    0   2.03 MBytes       
[  4]   4.00-5.00   sec   120 MBytes  1.01 Gbits/sec    0   2.59 MBytes       
[  4]   5.00-6.00   sec   119 MBytes  1.00 Gbits/sec    0   2.59 MBytes       
[  4]   6.00-7.00   sec   119 MBytes   998 Mbits/sec    0   2.72 MBytes       
[  4]   7.00-8.00   sec   119 MBytes  1.00 Gbits/sec    0   2.72 MBytes       
[  4]   8.00-9.00   sec   119 MBytes   999 Mbits/sec    0   2.72 MBytes       
[  4]   9.00-10.00  sec   119 MBytes  1.00 Gbits/sec  202   1.90 MBytes       
[  4]  10.00-10.51  sec  68.0 MBytes  1.12 Gbits/sec    0   1.90 MBytes       
---------------------------------------------------------------------------
[  4]   0.00-10.51  sec  1.22 GBytes   998 Mbits/sec  202             sender
[  4]   0.00-10.51  sec  1.22 GBytes   998 Mbits/sec                  receiver

```
Backplane1 is configured with fq_codel rate classifier that sometimes reorders packets, causing a few retransmits
So we'll need to just use pfifo_fast
The iperf3 client sent 10000 packets, with a (normal) retransmit rate of 202

```
# set some packet loss engine on nic
tc qdisc add dev backplane1 root netem loss random 2
# Cool uh ? This randomly drops 2% of the packets
```

Do it again

```
root@cpu-01:~# iperf3 -c 10.106.1.34 -k 10000 -b 1G 
Connecting to host 10.106.1.34, port 5201
[  4] local 10.106.1.11 port 58476 connected to 10.106.1.34 port 5201
[ ID] Interval           Transfer     Bandwidth       Retr  Cwnd
[  4]   0.00-1.00   sec  12.9 MBytes   108 Mbits/sec  219   3.80 KBytes       
[  4]   1.00-2.00   sec   216 MBytes  1.81 Gbits/sec  2716    217 KBytes       
[  4]   2.00-3.00   sec   119 MBytes   998 Mbits/sec  1536   57.1 KBytes       
[  4]   3.00-4.00   sec   100 MBytes   839 Mbits/sec  1033   7.61 KBytes       
[  4]   4.00-5.00   sec   115 MBytes   968 Mbits/sec  1345   5.71 KBytes       
[  4]   5.00-6.00   sec   129 MBytes  1.08 Gbits/sec  998    120 KBytes       
[  4]   6.00-7.00   sec  91.9 MBytes   771 Mbits/sec  1069   3.80 KBytes       
[  4]   7.00-8.00   sec   146 MBytes  1.23 Gbits/sec  1653   3.80 KBytes       
[  4]   8.00-9.00   sec  34.5 MBytes   289 Mbits/sec  433   3.80 KBytes       
[  4]   9.00-10.00  sec   100 MBytes   840 Mbits/sec  1026   3.80 KBytes       
[  4]  10.00-10.84  sec   185 MBytes  1.85 Gbits/sec  2089   62.8 KBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.84  sec  1.22 GBytes   968 Mbits/sec  14117             sender
[  4]   0.00-10.84  sec  1.22 GBytes   967 Mbits/sec                  receiver

```

After this test, one can see many retries, and a big reduction of the window size
Loss off packets is a big issue for tcp, which shows here

###  Alerts

  * WARNING when we see packet loss in the order of a few hundred Retr on client side (say 500)
  * ALERT when any number above

### iperf3 :

Iperf3 can generate json with a swath of info; what you want :

`end->sum->retransmits`


```
iperf3 -c 10.101.106.254 --format m -u -k 10000 -b 1000M -J
{
        "start":        {
                "connected":    [{
                                "socket":       4,
                                "local_host":   "10.106.1.11",
                                "local_port":   35178,
                                "remote_host":  "10.106.1.34",
                                "remote_port":  5201
                        }],
                "version":      "iperf 3.0.7",
                "system_info":  "Linux cpu-01.be-gen8-1 4.4.0-040400-generic #201601101930 SMP Mon Jan 11 00:32:41 UTC 2016 x86_64 x86_64 x86_64 GNU/Linux\n",
                "timestamp":    {
                        "time": "Fri, 09 Sep 2016 06:49:54 GMT",
                        "timesecs":     1473403794
                },
                "connecting_to":        {
                        "host": "10.106.1.34",
                        "port": 5201
                },
                "cookie":       "cpu-01.be-gen8-1.1473403794.589425.3",
                "tcp_mss_default":      1948,
                "test_start":   {
                        "protocol":     "TCP",
                        "num_streams":  1,
                        "blksize":      131072,
                        "omit": 0,
                        "duration":     0,
                        "bytes":        0,
                        "blocks":       10000,
                        "reverse":      0
                }
        },
        "intervals":    [{
                        "streams":      [{
                                        "socket":       4,
                                        "start":        0,
                                        "end":  1.00012,
                                        "seconds":      1.00012,
                                        "bytes":        107872256,
                                        "bits_per_second":      8.6287e+08,
                                        "retransmits":  770,
                                        "snd_cwnd":     3896,
                                        "omitted":      false
                                }],
                        "sum":  {
                                "start":        0,
                                "end":  1.00012,
                                "seconds":      1.00012,
                                "bytes":        107872256,
                                "bits_per_second":      8.6287e+08,
                                "retransmits":  770,
                                "omitted":      false
                        }
{
        "start":        {
                "connected":    [{
                                "socket":       4,
                                "local_host":   "10.106.1.11",
                                "local_port":   35178,
                                "remote_host":  "10.106.1.34",
                                "remote_port":  5201
                        }],
                "version":      "iperf 3.0.7",
                "system_info":  "Linux cpu-01.be-gen8-1 4.4.0-040400-generic #201601101930 SMP Mon Jan 11 00:32:41 UTC 2016 x86_64 x86_64 x86_64 GNU/Linux\n",
                "timestamp":    {
                        "time": "Fri, 09 Sep 2016 06:49:54 GMT",
                        "timesecs":     1473403794
                },
                "connecting_to":        {
                        "host": "10.106.1.34",
                        "port": 5201
                },
                "cookie":       "cpu-01.be-gen8-1.1473403794.589425.3",
                "tcp_mss_default":      1948,
                "test_start":   {
                        "protocol":     "TCP",
                        "num_streams":  1,
                        "blksize":      131072,
                        "omit": 0,
                        "duration":     0,
                        "bytes":        0,
                        "blocks":       10000,
                        "reverse":      0
                }
        },
        "intervals":    [{
                        "streams":      [{
                                        "socket":       4,
                                        "start":        0,
                                        "end":  1.00012,
                                        "seconds":      1.00012,
                                        "bytes":        107872256,
                                        "bits_per_second":      8.6287e+08,
                                        "retransmits":  770,
                                        "snd_cwnd":     3896,
                                        "omitted":      false
                                }],
                        "sum":  {
                                "start":        0,
                                "end":  1.00012,
                                "seconds":      1.00012,
                                "bytes":        107872256,
                                "bits_per_second":      8.6287e+08,
                                "retransmits":  770,
                                "omitted":      false
                        }
....
....
        "end":  {
                "streams":      [{
                                "sender":       {
                                        "socket":       4,
                                        "start":        0,
                                        "end":  10.6621,
                                        "seconds":      10.6621,
                                        "bytes":        1310720000,
                                        "bits_per_second":      9.8346e+08,
                                        "retransmits":  14432
                                },
                                "receiver":     {
                                        "socket":       4,
                                        "start":        0,
                                        "end":  10.6621,
                                        "seconds":      10.6621,
                                        "bytes":        1310694400,
                                        "bits_per_second":      9.83441e+08
                                }
                        }],
                "sum_sent":     {
                        "start":        0,
                        "end":  10.6621,
                        "seconds":      10.6621,
                        "bytes":        1310720000,
                        "bits_per_second":      9.8346e+08,
                        "retransmits":  14432
                },
                "sum_received": {
                        "start":        0,
                        "end":  10.6621,
                        "seconds":      10.6621,
                        "bytes":        1310694400,
                        "bits_per_second":      9.83441e+08
                },
                "cpu_utilization_percent":      {
                        "host_total":   11.5115,
                        "host_user":    0.148918,
                        "host_system":  11.355,
                        "remote_total": 0.170542,
                        "remote_user":  0.00320545,
                        "remote_system":        0.167324
                }
        }
}

```
That said, on a 40G link (i.e. the backplane for instance) you shouldn't see any loss for 1Gbit/sec
