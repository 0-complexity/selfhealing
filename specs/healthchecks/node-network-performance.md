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



