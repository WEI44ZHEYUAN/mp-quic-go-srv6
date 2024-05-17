#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.util import dumpNodeConnections

TC_QDISC_RATE = 20
TC_QDISC_LATENCY = 20

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
        r1 = self.addHost('r1', cls=FRR)
        r2 = self.addHost('r2', cls=FRR)
        r3 = self.addHost('r3', cls=FRR)
        r4 = self.addHost('r4', cls=FRR)
        r5 = self.addHost('r5', cls=FRR)
        client = self.addHost('client', ip=None)
        server = self.addHost('server', ip=None)
        
        # linkopts = dict(bw=10, delay='5ms', loss=10, max_queue_size=1000, use_htb=True)
        self.addLink(r1, r2, intfName1='r1-eth0', intfName2='r2-eth0')
        self.addLink(r3, r4, intfName1='r3-eth0', intfName2='r4-eth0')
        self.addLink(r2, r5, intfName1='r2-eth1', intfName2='r5-eth0')
        self.addLink(r4, r5, intfName1='r4-eth1', intfName2='r5-eth1')
        self.addLink(r3, r5, intfName1='r3-eth4', intfName2='r5-eth3')

        # client
        self.addLink( client, r1, intfName1='client-eth0', intfName2='r1-eth1')
        self.addLink( client, r3, intfName1='client-eth1', intfName2='r3-eth1')
    
        # server
        self.addLink( server, r5, intfName1='server-eth0', intfName2='r5-eth2')
        
def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(topo=topo)  # controller is used by s1-s3
    net.start()

    #configuration r1
    net[ 'r1' ].cmd("ip -6 addr add fc00:1::1/64 dev r1-eth1")
    net[ 'r1' ].cmd("ip -6 addr add fc00:a::1/64 dev r1-eth0")

    # net[ 'r1' ].cmd("tc qdisc add dev r1-eth0 root netem limit 1000 rate {0}Mbit".format(TC_QDISC_RATE))
    
    #configuration r2
    net[ 'r2' ].cmd("ip -6 addr add fc00:a::2/64 dev r2-eth0")
    net[ 'r2' ].cmd("ip -6 addr add fc00:c::1/64 dev r2-eth1")
    
    # net[ 'r2' ].cmd("tc qdisc add dev r2-eth0 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))

    #configuration r3
    net[ 'r3' ].cmd("ip -6 addr add fc00:2::1/64 dev r3-eth1")
    net[ 'r3' ].cmd("ip -6 addr add fc00:b::1/64 dev r3-eth0")
    net[ 'r3' ].cmd("ip -6 addr add fc00:e::1/64 dev r3-eth4")

    # net[ 'r3' ].cmd("tc qdisc add dev r3-eth0 root netem limit 1000 rate {0}Mbit".format(TC_QDISC_RATE))
    net[ 'r3' ].cmd("tc qdisc add dev r3-eth4 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))
    
    #configuration r4
    net[ 'r4' ].cmd("ip -6 addr add fc00:b::2/64 dev r4-eth0")
    net[ 'r4' ].cmd("ip -6 addr add fc00:d::1/64 dev r4-eth1")
   
    # net[ 'r4' ].cmd("tc qdisc add dev r4-eth0 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))

    #configuration r5
    net[ 'r5' ].cmd("ip -6 addr add fc00:c::2/64 dev r5-eth0")
    net[ 'r5' ].cmd("ip -6 addr add fc00:d::2/64 dev r5-eth1")
    net[ 'r5' ].cmd("ip -6 addr add fc00:3::1/64 dev r5-eth2")
    net[ 'r5' ].cmd("ip -6 addr add fc00:e::2/64 dev r5-eth3")

    #configuration client

    net[ 'client' ].cmd("ip -6 addr add fc00:1::2/64 dev client-eth0")
    net[ 'client' ].cmd("ip -6 addr add fc00:2::2/64 dev client-eth1")

    # This creates two different routing tables, that we use based on the source-address.
    net[ 'client' ].cmd("ip -6 rule add from fc00:1::2 table 1")
    net[ 'client' ].cmd("ip -6 rule add from fc00:2::2 table 2")
   
    # Configure the two different routing tables
    net[ 'client' ].cmd("ip -6 route add fc00:1::0/64 dev client-eth0 scope link table 1")
    net[ 'client' ].cmd("ip -6 route add default via fc00:1::1 dev client-eth0 table 1")

    net[ 'client' ].cmd("ip -6 route add fc00:2::0/64 dev client-eth1 scope link table 2")
    net[ 'client' ].cmd("ip -6 route add default via fc00:2::1 dev client-eth1 table 2")
    

    # default route for the selection process of normal internet-traffic
    net[ 'client' ].cmd("ip -6 route add default scope global nexthop via fc00:1::1 dev client-eth0")

    #configuration server
    net[ 'server' ].cmd("ip -6 addr add fc00:3::2/64 dev server-eth0")

    # This creates two different routing tables, that we use based on the source-address.
    net[ 'server' ].cmd("ip -6 rule add from fc00:3::2 table 1")
    # Configure the two different routing tables
    net[ 'server' ].cmd("ip -6 route add fc00:3::0/64 dev server-eth0 scope link table 1")
    net[ 'server' ].cmd("ip -6 route add default via fc00:3::1 dev server-eth0 table 1")

    # default route for the selection process of normal internet-traffic
    net[ 'server' ].cmd("ip -6 route add default scope global nexthop via fc00:3::1 dev server-eth0")

    print ("Dumping host connections")
    dumpNodeConnections( net.hosts )
    
    # add route

    net["r3"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:b::2,fc00:d::2,fc00:3::1:2 dev r3-eth0")
    net["r5"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r5-eth2")

    net["r5"].cmd("ip -6 route add fc00:2::2/128 encap seg6 mode encap segs fc00:d::1,fc00:b::1,fc00:2::1:2 dev r5-eth1")
    net["r3"].cmd("ip -6 route add fc00:2::1:2/128 encap seg6local action End.DX6 nh6 fc00:2::2 dev r3-eth1")

    net['r1'].vtysh_cmd(r1_conf)
    net['r2'].vtysh_cmd(r2_conf)
    net['r3'].vtysh_cmd(r3_conf)
    net['r4'].vtysh_cmd(r4_conf)
    net['r5'].vtysh_cmd(r5_conf)

    CLI( net )
    net.stop()

if __name__ == '__main__':

    setLogLevel( 'info' )
    run()