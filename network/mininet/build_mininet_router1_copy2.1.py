#!/usr/bin/python


import sys
import os
import argparse
sys.path.append(os.path.abspath('/home/zheyuan-w/Mp-Quic-Go/mpquic-sbd/network/'))
from networkx_workspace import networkx_stp
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections


#http://recolog.blogspot.com/2016/02/emulating-networks-with-routers-using.html
 
with_background = 1
number_of_interface_client = 2
download = False
playback = 'basic'
PATH_DIR = "/Mp-Quic-Go/mpquic-sbd/"

USER='zheyuan-w'


TC_QDISC_RATE = 20
TC_QDISC_LATENCY = 20
TC_QDISC_BURST = 2560
NICE = 'nice -n -10'
CLIENT = 'CLIENT'
SERVER = 'SERVER'
TIMEOUT = 35
TCP_CORE_MB = 100000


TC_QDISC_RATE2 = 2
TC_QDISC_LATENCY2 = 2

TC_QDISC_RATE = 20
daemons = """
zebra=yes
ospf6d=yes

vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
ospf6d_options=" --daemon -A ::1"
"""

vtysh = """
hostname {name}
service integrated-vtysh-config
"""

r1_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 1.1.1.1


interface r1-eth0 area 0.0.0.0
interface r1-eth1 area 0.0.0.0
"""

r2_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 2.2.2.2


interface r2-eth0 area 0.0.0.0
interface r2-eth1 area 0.0.0.0
"""

r3_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 3.3.3.3


interface r3-eth0 area 0.0.0.0
interface r3-eth1 area 0.0.0.0
interface r3-eth4 area 0.0.0.0
"""

r4_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 4.4.4.4


interface r4-eth0 area 0.0.0.0
interface r4-eth1 area 0.0.0.0
"""

r5_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 5.5.5.5


interface r5-eth0 area 0.0.0.0
interface r5-eth1 area 0.0.0.0
interface r5-eth2 area 0.0.0.0
interface r5-eth3 area 0.0.0.0
"""



# class LinuxRouter( Node ):
#     "A Node with IP forwarding enabled."

#     def config( self, **params ):
#         super( LinuxRouter, self).config( **params )
#         # Enable forwarding on the router
#         self.cmd( 'sysctl net.ipv4.ip_forward=1' )
#         self.cmd( 'sysctl -w net.ipv6.conf.all.forwarding=1' )
#         self.cmd( 'sysctl -w net.ipv6.conf.all.seg6_enabled=1' )
#         self.cmd( 'sysctl -w net.ipv6.conf.all.seg6_require_hmac=0' )

#     def terminate( self ):
#         self.cmd( 'sysctl net.ipv4.ip_forward=0' )
#         self.cmd( 'sysctl -w net.ipv6.conf.all.forwarding=0' )
#         super( LinuxRouter, self ).terminate()

class SRv6Node(Node):

    def __init__(self, name, **params):
        super().__init__(name, **params)

    def config(self, **params):
        self.cmd("ifconfig lo up")
        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.ipv6.conf.all.forwarding=1")
        self.cmd("sysctl -w net.ipv6.conf.all.seg6_enabled=1")
        self.cmd("sysctl -w net.ipv6.conf.all.seg6_require_hmac=0")

        for i in self.nameToIntf.keys():
            self.cmd("sysctl -w net.ipv6.conf.{}.seg6_enabled=1".format(i))

class FRR(SRv6Node):
    """FRR Node"""

    PrivateDirs = ["/etc/frr", "/var/run/frr"]

    def __init__(self, name, inNamespace=True, **params):
        params.setdefault("privateDirs", [])
        params["privateDirs"].extend(self.PrivateDirs)
        super().__init__(name, inNamespace=inNamespace, **params)
        
    def config(self, **params):
        super().config(**params)
        self.start_frr_service()

    def start_frr_service(self):
        """start FRR"""
        self.set_conf("/etc/frr/daemons", daemons)
        self.set_conf("/etc/frr/vtysh.conf", vtysh.format(name=self.name))
        print(self.cmd("/usr/lib/frr/frrinit.sh start"))

    def set_conf(self, file, conf):
        """set frr config"""
        self.cmd("""\
cat << 'EOF' | tee {}
{}
EOF""".format(file, conf))

    def vtysh_cmd(self, cmd=""):
        """exec vtysh commands"""
        cmds = cmd.split("\n")
        vtysh_cmd = "vtysh"
        for c in cmds:
            vtysh_cmd += " -c \"{}\"".format(c)
        return self.cmd(vtysh_cmd)

class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):
        r1 = self.addHost('r1', cls=FRR, ip='10.0.0.1/30')
        r2 = self.addHost('r2', cls=FRR, ip='10.0.0.2/30')
        r3 = self.addHost('r3', cls=FRR, ip='10.0.0.5/30')
        r4 = self.addHost('r4', cls=FRR, ip='10.0.0.6/30')
        r5 = self.addHost('r5', cls=FRR, ip='10.0.0.9/30')
        client = self.addHost('client', ip='10.0.1.2/24', defaultRoute='via 10.0.1.1')
        server = self.addHost('server', ip='10.0.2.2/24', defaultRoute='via 10.0.2.1')
        client1 = self.addHost('client1', ip='10.0.5.2/24', defaultRoute='via 10.0.5.1')
        client2 = self.addHost('client2', ip='10.0.7.2/24', defaultRoute='via 10.0.7.1')
        server1 = self.addHost('server1', ip='10.0.6.2/24', defaultRoute='via 10.0.6.1')
        server2 = self.addHost('server2', ip='10.0.8.2/24', defaultRoute='via 10.0.8.1')
        
        # linkopts = dict(bw=10, delay='5ms', loss=10, max_queue_size=1000, use_htb=True)
        self.addLink(r1, r2, intfName1='r1-eth0', intfName2='r2-eth0')
        self.addLink(r3, r4, intfName1='r3-eth0', intfName2='r4-eth0')
        self.addLink(r2, r5, intfName1='r2-eth1', params1={ 'ip' : '10.0.0.9/30' }, intfName2='r5-eth0', params2={ 'ip' : '10.0.0.10/30' })
        self.addLink(r4, r5, intfName1='r4-eth1', params1={ 'ip' : '10.0.0.13/30' }, intfName2='r5-eth1', params2={ 'ip' : '10.0.0.14/30' })
        self.addLink(r3, r5, intfName1='r3-eth4', params1={ 'ip' : '10.0.0.3/30' }, intfName2='r5-eth3', params2={ 'ip' : '10.0.0.4/30' })

        # client
        self.addLink( client, r1, intfName2='r1-eth1', params2={ 'ip' : '10.0.1.1/24' } )
        self.addLink( client, r3, intfName1='client-eth1', params1={ 'ip' : '10.0.3.2/24' }, intfName2='r3-eth1', params2={ 'ip' : '10.0.3.1/24' } )

        if number_of_interface_client > 2:
            self.addLink( client, r1, intfName1='client-eth2', params1={ 'ip' : '10.0.9.2/24' }, intfName2='r1-eth3', params2={ 'ip' : '10.0.9.1/24' } )

        if number_of_interface_client > 3:
            self.addLink( client, r3, intfName1='client-eth3', params1={ 'ip' : '10.0.11.2/24' }, intfName2='r3-eth3', params2={ 'ip' : '10.0.11.1/24' } )

        if number_of_interface_client > 4:
            self.addLink( client, r1, intfName1='client-eth4', params1={ 'ip' : '10.0.13.2/24' }, intfName2='r1-eth4', params2={ 'ip' : '10.0.13.1/24' } )

        # server
        self.addLink( server, r5, intfName2='r5-eth2', params2={ 'ip' : '10.0.2.1/24' } )
        

        self.addLink( client1, r1, intfName2='r1-eth2', params2={ 'ip' : '10.0.5.1/24' } )
        self.addLink( client2, r3, intfName2='r3-eth2', params2={ 'ip' : '10.0.7.1/24' } )

        self.addLink( server1, r2, intfName2='r2-eth2', params2={ 'ip' : '10.0.6.1/24' } )
        self.addLink( server2, r4, intfName2='r4-eth2', params2={ 'ip' : '10.0.8.1/24' } )

def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(topo=topo)  # controller is used by s1-s3
    net.start()

    #configuration r1
    net[ 'r1' ].cmd("ip -6 addr add fc00:1::1/64 dev r1-eth1")
    net[ 'r1' ].cmd("ip -6 addr add fc00:a::1/64 dev r1-eth0")
    # net[ 'r1' ].cmd("ip -6 route add default via fc00:a::2")
    # net[ 'r1' ].cmd("ip -6 route add fc00:2::0/64 via fc00:1::2 dev r1-eth1")
    net[ 'r1' ].cmd("tc qdisc add dev r1-eth0 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY2, TC_QDISC_RATE2))

    net[ 'r1' ].cmd("ifconfig r1-eth2 10.0.5.1/24")
    # net[ 'r1' ].cmd("route add default gw 10.0.0.2")
    # net[ 'r1' ].cmd("tc qdisc add dev r1-eth0 root netem limit 1000 rate {0}Mbit".format(TC_QDISC_RATE))
    

    # for i in [3, 11]:
    #    net[ 'r1' ].cmd("route add -net 10.0.{0}.0 netmask 255.255.255.0 gw 10.0.1.2".format(i))

    #configuration r2
    net[ 'r2' ].cmd("ip -6 addr add fc00:a::2/64 dev r2-eth0")
    net[ 'r2' ].cmd("ip -6 addr add fc00:c::1/64 dev r2-eth1")
    # net[ 'r2' ].cmd("ip -6 route add default via fc00:a::1")
    # net[ 'r2' ].cmd("ip -6 route add fc00:3::0/64 via fc00:c::2 dev r2-eth1")

    net[ 'r2' ].cmd("ifconfig r2-eth2 10.0.6.1/24")
    # net[ 'r2' ].cmd("route add default gw 10.0.0.1")
    # net[ 'r2' ].cmd("ip route add 10.0.2.0/24 via 10.0.0.10 dev r2-eth1")
    
   
    # net[ 'r2' ].cmd("tc qdisc add dev r2-eth0 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))

    #configuration r3
    net[ 'r3' ].cmd("ip -6 addr add fc00:2::1/64 dev r3-eth1")
    net[ 'r3' ].cmd("ip -6 addr add fc00:b::1/64 dev r3-eth0")
    net[ 'r3' ].cmd("ip -6 addr add fc00:e::1/64 dev r3-eth4")
    # net[ 'r3' ].cmd("ip -6 route add default via fc00:b::2")
    # net[ 'r3' ].cmd("ip -6 route add fc00:1::0/64 via fc00:2::2 dev r3-eth1")

    net[ 'r3' ].cmd("ifconfig r3-eth2 10.0.7.1/24")
    # net[ 'r3' ].cmd("route add default gw 10.0.0.6")
    # net[ 'r3' ].cmd("tc qdisc add dev r3-eth0 root netem limit 1000 rate {0}Mbit".format(TC_QDISC_RATE))
    net[ 'r3' ].cmd("tc qdisc add dev r3-eth4 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))
    # for i in [1, 9, 13]:
    #    net[ 'r3' ].cmd("route add -net 10.0.{0}.0 netmask 255.255.255.0 gw 10.0.3.2".format(i))

    #configuration r4
    net[ 'r4' ].cmd("ip -6 addr add fc00:b::2/64 dev r4-eth0")
    net[ 'r4' ].cmd("ip -6 addr add fc00:d::1/64 dev r4-eth1")
    # net[ 'r4' ].cmd("ip -6 route add default via fc00:b::1")
    # net[ 'r4' ].cmd("ip -6 route add fc00:3::0/64 via fc00:d::2 dev r4-eth1")

    net[ 'r4' ].cmd("ifconfig r4-eth2 10.0.8.1/24")    
    # net[ 'r4' ].cmd("route add default gw 10.0.0.5")
    # net[ 'r4' ].cmd("route add -net 10.0.2.0 netmask 255.255.255.0 gw 10.0.0.14")
    # net[ 'r4' ].cmd("tc qdisc add dev r4-eth0 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))

    #configuration r5
    net[ 'r5' ].cmd("ip -6 addr add fc00:c::2/64 dev r5-eth0")
    net[ 'r5' ].cmd("ip -6 addr add fc00:d::2/64 dev r5-eth1")
    net[ 'r5' ].cmd("ip -6 addr add fc00:3::1/64 dev r5-eth2")
    net[ 'r5' ].cmd("ip -6 addr add fc00:e::2/64 dev r5-eth3")
    # net[ 'r5' ].cmd("ip -6 route add default via fc00:c::1")
    # net[ 'r5' ].cmd("ip -6 route add fc00:1::0/64 via fc00:c::1 dev r5-eth0")
    # net[ 'r5' ].cmd("ip -6 route add fc00:2::0/64 via fc00:d::1 dev r5-eth1")


    net[ 'r5' ].cmd("ifconfig r5-eth0 10.0.0.10/30")    
    net[ 'r5' ].cmd("ifconfig r5-eth2 10.0.2.1/24")    
    # net[ 'r5' ].cmd("route add default gw 10.0.0.9")

    # for i in [1, 9, 13]:
    #     net[ 'r5' ].cmd("route add -net 10.0.{0}.0 netmask 255.255.255.0 gw 10.0.0.9".format(i))

    # for i in [3, 11]:
    #     net[ 'r5' ].cmd("route add -net 10.0.{0}.0 netmask 255.255.255.0 gw 10.0.0.13".format(i))

    
    #configuration client

    net[ 'client' ].cmd("ip -6 addr add fc00:1::2/64 dev client-eth0")
    net[ 'client' ].cmd("ip -6 addr add fc00:2::2/64 dev client-eth1")

    # This creates two different routing tables, that we use based on the source-address.
    net[ 'client' ].cmd("ip rule add from 10.0.1.2 table 1")
    net[ 'client' ].cmd("ip -6 rule add from fc00:1::2 table 1")
    net[ 'client' ].cmd("ip rule add from 10.0.3.2 table 2")
    net[ 'client' ].cmd("ip -6 rule add from fc00:2::2 table 2")
    # Configure the two different routing tables
    net[ 'client' ].cmd("ip route add 10.0.1.0/24 dev client-eth0 scope link table 1")
    net[ 'client' ].cmd("ip -6 route add fc00:1::0/64 dev client-eth0 scope link table 1")
    net[ 'client' ].cmd("ip route add default via 10.0.1.1 dev client-eth0 table 1")
    net[ 'client' ].cmd("ip -6 route add default via fc00:1::1 dev client-eth0 table 1")

    net[ 'client' ].cmd("ip route add 10.0.3.0/24 dev client-eth1 scope link table 2")
    net[ 'client' ].cmd("ip -6 route add fc00:2::0/64 dev client-eth1 scope link table 2")
    net[ 'client' ].cmd("ip route add default via 10.0.3.1 dev client-eth1 table 2")
    net[ 'client' ].cmd("ip -6 route add default via fc00:2::1 dev client-eth1 table 2")
    
    if number_of_interface_client > 2:
        net[ 'client' ].cmd("ip rule add from 10.0.9.2 table 3")
        net[ 'client' ].cmd("ip route add 10.0.9.0/24 dev client-eth2 scope link table 3")
        net[ 'client' ].cmd("ip route add default via 10.0.9.1 dev client-eth2 table 3")
        # net[ 'r5' ].cmd("ip route add 10.0.9.0/24 via 10.0.0.10 dev r5-eth0")
    if number_of_interface_client > 3:
        net[ 'client' ].cmd("ip rule add from 10.0.11.2 table 4")
        net[ 'client' ].cmd("ip route add 10.0.11.0/24 dev client-eth3 scope link table 4")
        net[ 'client' ].cmd("ip route add default via 10.0.11.1 dev client-eth3 table 4")
        # net[ 'r5' ].cmd("ip route add 10.0.11.0/24 via 10.0.0.14 dev r5-eth1")
    if number_of_interface_client > 4:
        net[ 'client' ].cmd("ip rule add from 10.0.13.2 table 5")
        net[ 'client' ].cmd("ip route add 10.0.13.0/24 dev client-eth4 scope link table 5")
        net[ 'client' ].cmd("ip route add default via 10.0.13.1 dev client-eth4 table 5")
        # net[ 'r5' ].cmd("ip route add 10.0.13.0/24 via 10.0.0.10 dev r5-eth1")


    # default route for the selection process of normal internet-traffic
    net[ 'client' ].cmd("ip route add default scope global nexthop via 10.0.1.1 dev client-eth0")
    net[ 'client' ].cmd("ip -6 route add default scope global nexthop via fc00:1::1 dev client-eth0")

    #configuration server
    net[ 'server' ].cmd("ip -6 addr add fc00:3::2/64 dev server-eth0")

    # This creates two different routing tables, that we use based on the source-address.
    net[ 'server' ].cmd("ip rule add from 10.0.2.2 table 1")
    net[ 'server' ].cmd("ip -6 rule add from fc00:3::2 table 1")
    # Configure the two different routing tables
    net[ 'server' ].cmd("ip route add 10.0.2.0/24 dev server-eth0 scope link table 1")
    net[ 'server' ].cmd("ip -6 route add fc00:3::0/64 dev server-eth0 scope link table 1")
    net[ 'server' ].cmd("ip route add default via 10.0.2.1 dev server-eth0 table 1")
    net[ 'server' ].cmd("ip -6 route add default via fc00:3::1 dev server-eth0 table 1")

    # default route for the selection process of normal internet-traffic
    net[ 'server' ].cmd("ip route add default scope global nexthop via 10.0.2.1 dev server-eth0")
    net[ 'server' ].cmd("ip -6 route add default scope global nexthop via fc00:3::1 dev server-eth0")

    print ("Dumping host connections")
    dumpNodeConnections( net.hosts )
    
    # add route
    network_graph = networkx_stp.Networkx()

    FROUTE_NAME = network_graph.shortest_path_hn(0)
    BROUTE_NAME = network_graph.shortest_path_hn(1)

    FROUTE_IP = network_graph.shortest_path_ip(0)
    BROUTE_IP = network_graph.shortest_path_ip(1)

    FROUTE_IF = network_graph.shortest_path_if(0)
    BROUTE_IF = network_graph.shortest_path_if(1)

    FROUTE_IF_DECAP = network_graph.shortest_path_if_decap(0)
    BROUTE_IF_DECAP = network_graph.shortest_path_if_decap(1)

    FVIRTUAL_IP = network_graph.random_virtual_ip(0)
    BVIRTUAL_IP = network_graph.random_virtual_ip(1)

    FDESTINATION_IP = network_graph.destination_ip(0)
    BDESTINATION_IP = network_graph.destination_ip(1)
    
############################### example for dynamic route

    # net["{0}".format(FROUTE_NAME[0][0])].cmd("ip -6 route add {0}/128 encap seg6 mode encap segs {1},{2} dev {3}".format(FDESTINATION_IP[0],FROUTE_IP[0], FVIRTUAL_IP[0],FROUTE_IF[0]))
    # net["{0}".format(FROUTE_NAME[0][-1])].cmd("ip -6 route add {0}/128 encap seg6local action End.DX6 nh6 {1} dev {2}".format(FVIRTUAL_IP[0],FDESTINATION_IP[0],FROUTE_IF_DECAP[0]))

    # net["{0}".format(BROUTE_NAME[0][0])].cmd("ip -6 route add {0}/128 encap seg6 mode encap segs {1},{2} dev {3}".format(BDESTINATION_IP[0],BROUTE_IP[0],BVIRTUAL_IP[0], BROUTE_IF[0]))
    # net["{0}".format(BROUTE_NAME[0][-1])].cmd("ip -6 route add {0}/128 encap seg6local action End.DX6 nh6 {1} dev {2}".format(BVIRTUAL_IP[0],BDESTINATION_IP[0],BROUTE_IF_DECAP[0]))


    # net["{0}".format(FROUTE_NAME[1][0])].cmd("ip -6 route add {0}/128 encap seg6 mode encap segs {1},{2} dev {3}".format(FDESTINATION_IP[1],FROUTE_IP[1], FVIRTUAL_IP[1],FROUTE_IF[1]))
    # net["{0}".format(FROUTE_NAME[1][-1])].cmd("ip -6 route add {0}/128 encap seg6local action End.DX6 nh6 {1} dev {2}".format(FVIRTUAL_IP[1],FDESTINATION_IP[1],FROUTE_IF_DECAP[1]))

    # net["{0}".format(BROUTE_NAME[1][0])].cmd("ip -6 route add {0}/128 encap seg6 mode encap segs {1},{2} dev {3}".format(BDESTINATION_IP[1],BROUTE_IP[1],BVIRTUAL_IP[1], BROUTE_IF[1]))
    # net["{0}".format(BROUTE_NAME[1][-1])].cmd("ip -6 route add {0}/128 encap seg6local action End.DX6 nh6 {1} dev {2}".format(BVIRTUAL_IP[1],BDESTINATION_IP[1],BROUTE_IF_DECAP[1]))

############################### example for route r3 to server and back with out decap
    
    # net["r3"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:b::2,fc00:d::2 dev r3-eth0")
    # net["r5"].cmd("ip -6 route add fc00:2::2/128 encap seg6 mode encap segs fc00:d::1,fc00:b::1 dev r5-eth1")

############################### example for route r1 to server and back
    
    net["r1"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:a::2,fc00:c::2,fc00:3::1:2 dev r1-eth0")
    net["r5"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r5-eth2")

    net["r5"].cmd("ip -6 route add fc00:1::2/128 encap seg6 mode encap segs fc00:c::1,fc00:a::1,fc00:1::1:2 dev r5-eth0")
    net["r1"].cmd("ip -6 route add fc00:1::1:2/128 encap seg6local action End.DX6 nh6 fc00:1::2 dev r1-eth1")

############################### example for route r3 to server and back
    
    # net["r3"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:b::2,fc00:d::2,fc00:3::1:2 dev r3-eth0")
    # net["r5"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r5-eth2")

    # net["r5"].cmd("ip -6 route add fc00:2::2/128 encap seg6 mode encap segs fc00:d::1,fc00:b::1,fc00:2::1:2 dev r5-eth1")
    # net["r3"].cmd("ip -6 route add fc00:2::1:2/128 encap seg6local action End.DX6 nh6 fc00:2::2 dev r3-eth1")


    net['r1'].vtysh_cmd(r1_conf)
    net['r2'].vtysh_cmd(r2_conf)
    net['r3'].vtysh_cmd(r3_conf)
    net['r4'].vtysh_cmd(r4_conf)
    net['r5'].vtysh_cmd(r5_conf)

    CLI( net )
    net.stop()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Mode execute Mininet')
    parser.add_argument('--background', '-b',
                   metavar='background',
                   type=int,
                   default=1,
                   help='execute with background or not')

    parser.add_argument('--number_client', '-nm',
                   metavar='number_client',
                   type=int,
                   default=2,
                   help='the number of interface client')

    parser.add_argument('--download', '-d',
                   metavar='download',
                   type=bool,
                   default=False,
                   help="Keep the video files after playback")

    parser.add_argument('--playback', '-p',
                   metavar='playback',
                   type=str,
                   default='basic',
                   help="Playback type (basic, sara, netflix, or all)")


    # Execute the parse_args() method
    args                       = parser.parse_args()
    with_background            = args.background
    number_of_interface_client = args.number_client
    download                   = args.download
    playback                   = args.playback

    # if len(sys.argv) > 1:
    #     with_background = int(sys.argv[1])
    # if len(sys.argv) > 2:
    #     number_of_interface_client = int(sys.argv[2])

    setLogLevel( 'info' )
    run()
