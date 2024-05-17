#!/usr/bin/python

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import Node
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
from mininet.link import TCLink

TC_QDISC_RATE = 1
TC_QDISC_LATENCY = 0

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
interface r1-eth7 area 0.0.0.0
"""

r2_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 2.2.2.2


interface r2-eth0 area 0.0.0.0
interface r2-eth4 area 0.0.0.0
"""

r3_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 3.3.3.3


interface r3-eth0 area 0.0.0.0
interface r3-eth5 area 0.0.0.0
"""

r4_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 4.4.4.4


interface r4-eth2 area 0.0.0.0
interface r4-eth6 area 0.0.0.0
"""


r5_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 5.5.5.5


interface r5-eth3 area 0.0.0.0
interface r5-eth6 area 0.0.0.0
"""


r6_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 6.6.6.6

interface r6-eth0 area 0.0.0.0
interface r6-eth4 area 0.0.0.0
interface r6-eth5 area 0.0.0.0
interface r6-eth7 area 0.0.0.0
"""

r7_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 7.7.7.7


interface r7-eth1 area 0.0.0.0
interface r7-eth6 area 0.0.0.0
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


    def build(self, **_opts):
    # add frr node
        r1 = self.addHost("r1", cls=FRR)
        r2 = self.addHost("r2", cls=FRR)
        r3 = self.addHost("r3", cls=FRR)
        r4 = self.addHost("r4", cls=FRR)
        r5 = self.addHost("r5", cls=FRR)
        r6 = self.addHost("r6", cls=FRR)
        r7 = self.addHost("r7", cls=FRR)
        
        # host
        h1 = self.addHost("h1", ip=None)
        h3 = self.addHost("h3", ip=None)

        # config link
        self.addLink(r1, h1, intfName1="r1-eth0", intfName2="h1-eth1")

        self.addLink(r2, h1, intfName1="r2-eth0", intfName2="h1-eth2")
    
        self.addLink(r3, h1, intfName1="r3-eth0", intfName2="h1-eth3")
    
        self.addLink(r6, h3, intfName1="r6-eth0", intfName2="h3-eth6")

        self.addLink(r1, r7, intfName1="r1-eth7", intfName2="r7-eth1", bw = 150, delay = '300ms')

        self.addLink(r7, r6, intfName1="r7-eth6", intfName2="r6-eth7")
        
        self.addLink(r2, r4, intfName1="r2-eth4", intfName2="r4-eth2", bw = 150)

        self.addLink(r4, r6, intfName1="r4-eth6", intfName2="r6-eth4")

        self.addLink(r3, r5, intfName1="r3-eth5", intfName2="r5-eth3", bw = 150)        

        self.addLink(r5, r6, intfName1="r5-eth6", intfName2="r6-eth5")

def run():

    topo = NetworkTopo()
    net = Mininet(topo=topo, link=TCLink)
    net.start()

    # set address
   
    # r1
    net['r1'].cmd("ip -6 addr add fc00:1::1/64 dev r1-eth0")
    net['r1'].cmd("ip -6 addr add fc00:a::2/64 dev r1-eth7")
    # net['r1'].cmd("tc qdisc add dev r1-eth7 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))

    # r2
    net['r2'].cmd("ip -6 addr add fc00:2::1/64 dev r2-eth0")
    net['r2'].cmd("ip -6 addr add fc00:c::2/64 dev r2-eth4")
    # net['r2'].cmd("tc qdisc add dev r2-eth4 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))

    # r3
    net['r3'].cmd("ip -6 addr add fc00:4::1/64 dev r3-eth0")
    net['r3'].cmd("ip -6 addr add fc00:e::2/64 dev r3-eth5")
    # net['r3'].cmd("tc qdisc add dev r3-eth5 root netem limit 67 delay {0}ms rate {1}Mbit".format(TC_QDISC_LATENCY, TC_QDISC_RATE))
    
    # r4
    net['r4'].cmd("ip -6 addr add fc00:c::1/64 dev r4-eth2")
    net['r4'].cmd("ip -6 addr add fc00:d::2/64 dev r4-eth6")

    # r5
    net['r5'].cmd("ip -6 addr add fc00:e::1/64 dev r5-eth3")
    net['r5'].cmd("ip -6 addr add fc00:f::2/64 dev r5-eth6")

    # r6
    net['r6'].cmd("ip -6 addr add fc00:3::1/64 dev r6-eth0")
    net['r6'].cmd("ip -6 addr add fc00:b::1/64 dev r6-eth7")
    net['r6'].cmd("ip -6 addr add fc00:d::1/64 dev r6-eth4")
    net['r6'].cmd("ip -6 addr add fc00:f::1/64 dev r6-eth5")

    # r7
    net['r7'].cmd("ip -6 addr add fc00:a::1/64 dev r7-eth1")
    net['r7'].cmd("ip -6 addr add fc00:b::2/64 dev r7-eth6")


    #config route
    # h1
    net['h1'].cmd("ip -6 addr add fc00:1::2/64 dev h1-eth1")
    net['h1'].cmd("ip -6 addr add fc00:2::2/64 dev h1-eth2")
    net['h1'].cmd("ip -6 addr add fc00:4::2/64 dev h1-eth3")

    net['h1'].cmd("ip -6 rule add from fc00:1::2 table 1")
    net['h1'].cmd("ip -6 route add fc00:1::0/64 dev h1-eth1 scope link table 1")
    net['h1'].cmd("ip -6 route add default via fc00:1::1 dev h1-eth1 table 1")

    net['h1'].cmd("ip -6 rule add from fc00:2::2 table 2")
    net['h1'].cmd("ip -6 route add fc00:2::0/64 dev h1-eth2 scope link table 2")
    net['h1'].cmd("ip -6 route add default via fc00:2::1 dev h1-eth2 table 2")

    net['h1'].cmd("ip -6 rule add from fc00:4::2 table 3")
    net['h1'].cmd("ip -6 route add fc00:4::0/64 dev h1-eth3 scope link table 3")
    net['h1'].cmd("ip -6 route add default via fc00:4::1 dev h1-eth3 table 3")

    net['h1'].cmd("ip -6 route add default scope global nexthop via fc00:1::1 dev h1-eth1")

    # h3
    net['h3'].cmd("ip -6 addr add fc00:3::2/64 dev h3-eth6")

    net['h3'].cmd("ip -6 rule add from fc00:3::2 table 1")
    net['h3'].cmd("ip -6 route add fc00:3::0/64 dev h3-eth6 scope link table 1")
    net['h3'].cmd("ip -6 route add default via fc00:3::1 dev h3-eth6 table 1")

    net['h3'].cmd("ip -6 route add default scope global nexthop via fc00:3::1 dev h3-eth6")
    
    dumpNodeConnections( net.hosts )

    # add route

    # # r2 route
    # # forward
    # net["r2"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:c::1,fc00:d::1,fc00:3::1:2 dev r2-eth4")
    # net["r6"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r6-eth0")

    # # backward
    # net["r6"].cmd("ip -6 route add fc00:2::2/128 encap seg6 mode encap segs fc00:d::2,fc00:c::2,fc00:2::1:2 dev r6-eth4")
    # net["r2"].cmd("ip -6 route add fc00:2::1:2/128 encap seg6local action End.DX6 nh6 fc00:2::2 dev r2-eth0")


    # # r3 route
    # # forward
    # net["r3"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:e::1,fc00:f::1,fc00:3::1:2 dev r3-eth5")
    # net["r6"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r6-eth0")
    
    # # backward
    # net["r6"].cmd("ip -6 route add fc00:4::2/128 encap seg6 mode encap segs fc00:f::2,fc00:e::2,fc00:4::1:2 dev r6-eth5")
    # net["r3"].cmd("ip -6 route add fc00:4::1:2/128 encap seg6local action End.DX6 nh6 fc00:4::2 dev r3-eth0")

    # net["r1"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:c::2,fc00:f::2,fc00:3::1:2 dev r1_r7")
    # net["r6"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r6_h3")

    # net["r2"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:d::2,fc00:dd::2,fc00:3::1:2 dev r2_r4")
    # net["r6"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r6_h3")

    # net["r3"].cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:e::2,fc00:ee::2,fc00:3::1:2 dev r3_r5")
    # net["r6"].cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r6_h3")

    
    

    net['r1'].vtysh_cmd(r1_conf)
    net['r2'].vtysh_cmd(r2_conf)
    net['r3'].vtysh_cmd(r3_conf)
    net['r4'].vtysh_cmd(r4_conf)
    net['r5'].vtysh_cmd(r5_conf)
    net['r6'].vtysh_cmd(r6_conf)
    net['r7'].vtysh_cmd(r7_conf)

    CLI(net)
    net.stop()


if __name__ == "__main__":

    setLogLevel("info")
    run()
