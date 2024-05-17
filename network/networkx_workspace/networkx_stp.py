import random
import sys
sys.dont_write_bytecode = True

import networkx as nx

import matplotlib.pyplot as plt

class Networkx:

    def __init__(self):

        self.graph = nx.Graph()
        self.graph.add_edge('client', 'r1')
        self.graph.add_edge('client', 'r3')
        self.graph.add_edge('r1', 'r2')
        self.graph.add_edge('r3', 'r4')
        self.graph.add_edge('r3', 'r5', delay=20)
        self.graph.add_edge('r4', 'r5')
        self.graph.add_edge('r2', 'r5')
        self.graph.add_edge('r5', 'server')

        # adding attribute to the node and egde
        ip = {('client', 'r1'): {'ip1': 'fc00:1::2', 'ip2': 'fc00:1::1', 'if1': 'client-eth0', 'if2': 'r1-eth1'}, 
            ('client','r3'): {'ip1': 'fc00:2::2', 'ip2': 'fc00:2::1', 'if1': 'client-eth1', 'if2': 'r3-eth1'}, 
            ('r1','r2'): {'ip1': 'fc00:a::1', 'ip2': 'fc00:a::2', 'if1': 'r1-eth0', 'if2': 'r2-eth0'}, 
            ('r3','r4'): {'ip1': 'fc00:b::1', 'ip2': 'fc00:b::2', 'if1': 'r3-eth0', 'if2': 'r4-eth0'}, 
            ('r3','r5'): {'ip1': 'fc00:e::1', 'ip2': 'fc00:e::2', 'if1': 'r3-eth4', 'if2': 'r5-eth3'}, 
            ('r4','r5'): {'ip1': 'fc00:d::1', 'ip2': 'fc00:d::2', 'if1': 'r4-eth1', 'if2': 'r5-eth1'}, 
            ('r2','r5'): {'ip1': 'fc00:c::1', 'ip2': 'fc00:c::2', 'if1': 'r2-eth1', 'if2': 'r5-eth0'}, 
            ('r5','server'): {'ip1': 'fc00:3::1', 'ip2': 'fc00:3::2', 'if1': 'r5-eth2', 'if2': 'server-eth0'}}
        nx.set_edge_attributes(self.graph, ip)


    def shortest_path(self,num):

        paths = list(nx.shortest_simple_paths(self.graph, 'client', 'server', weight='delay'))
  
        lstName = []
        lstValue = []

        for path in paths[:2]:
            # print(path)
            lst = []
            for ip in range(len(path) - 1):
                lst.append(self.graph[path[ip]][path[ip + 1]]['ip2'])
            # print(lst)
            print('------------------------------------------')
            print(lst)
            print('------------------------------------------')
            lstValue.append(lst)
            print('------------------------------------------')
            print(path)
            print('------------------------------------------')
            lstName.append(path)
        if num == 0:
            return lstValue 
        else:
            return lstName
        

    def shortest_path_1(self):

        paths = list(nx.shortest_simple_paths(self.graph, 'client', 'server', weight='delay'))
        paths2 = []

        for path in paths[:2]:

            paths2.append(path)
        
        return paths2

    def shortest_path_hn(self,n):
        
        paths = self.shortest_path_1()
        for path in paths:
            path.pop()
            path.pop(0)

        if n == 0:
            print(paths)
            return paths
        
        elif n == 1:
            paths = [list(reversed(sublist)) for sublist in paths]
            print(paths)
            return paths
    


    def shortest_path_ip(self,n):

        paths = self.shortest_path_1()

        ip_l = []

        for path in paths:
            path.pop()
            path.pop(0)
            temp = []
            if n == 0:
                for ip in range(len(path)-1):
                    ipa = 'ip2'
                    temp.append(self.graph[path[ip]][path[ip + 1]][ipa])
                   
            elif n == 1:
                for ip in range(len(path)-1):
                    ipa = 'ip1'    
                    temp.append(self.graph[path[ip]][path[ip + 1]][ipa])
                temp = list(reversed(temp))    

            ip_l.append(','.join(map(str,temp)))
            
            
        print(ip_l)    
        return ip_l
        
    def shortest_path_if(self,n):

        paths = self.shortest_path_1()

        if_l = []

        for path in paths:
            path.pop()
            path.pop(0)
            if n == 0:
                ifname = 'if1'
                if_l.append(self.graph[path[0]][path[1]][ifname])
            elif n == 1:
                path = list(reversed(path))
                ifname = 'if2'
                if_l.append(self.graph[path[0]][path[1]][ifname])


        print(if_l)
        return if_l
    
    def shortest_path_if_decap(self,n):

        paths = self.shortest_path_1()

        ifd_l = []

        for path in paths:
            if n == 0:
                ifd = 'if1'
                ifd_l.append(self.graph[path[-2]][path[-1]][ifd])
            elif n == 1:
                path = list(reversed(path))
                ifd = 'if2'
                ifd_l.append(self.graph[path[-2]][path[-1]][ifd])

        print(ifd_l)
        return ifd_l

    def random_virtual_ip(self,n):

        paths = self.shortest_path_1()
        vip_l = []
        for path in paths:
            if n == 0 :
                vip = 'ip1'
                vip_l.append(self.graph[path[-2]][path[-1]][vip]+':2')
            elif n == 1 :
                path = list(reversed(path))
                vip = 'ip2'
                vip_l.append(self.graph[path[-2]][path[-1]][vip]+':2')

        print(vip_l)

        return vip_l
    
    def destination_ip(self,n):

        paths = self.shortest_path_1()
        dst_ip = []
        for path in paths:
            if n == 0 :
                dst = 'ip2'
                dst_ip.append(self.graph[path[-2]][path[-1]][dst])
            elif n == 1 :
                path = list(reversed(path))
                dst = 'ip1'
                dst_ip.append(self.graph[path[-2]][path[-1]][dst])

        print(dst_ip)
        return dst_ip

    def create_graph(self):
        # explicitly set positions
        pos = {'client': (-1, 0), 'r1': (3, 3), 'r3': (3, -3), 'r2': (9, 3), 'r4': (9, -3), 'r5': (9, 0), 'server': (15, 0)}

        options = {
            "font_size": 12,
            "node_size": 2000,
            "node_color": "white",
            "edgecolors": "black",
            "linewidths": 5,
            "width": 5,
        }
        nx.draw_networkx(self.graph, pos, **options)

        # Set margins for the axes so that nodes aren't clipped
        ax = plt.gca()
        ax.margins(0.20)
        plt.axis("off")
        plt.savefig('mygraph.png')
        
        