import sys
sys.dont_write_bytecode = True

import networkx as nx

import matplotlib.pyplot as plt

def mod(num):

    G = nx.Graph()
    G.add_edge('client', 'r1', weight=5)
    G.add_edge('client', 'r3')
    G.add_edge('r1', 'r2')
    G.add_edge('r3', 'r4')
    G.add_edge('r3', 'r5', weight=20)
    G.add_edge('r4', 'r5')
    G.add_edge('r2', 'r5')
    G.add_edge('r5', 'server')

    # adding attribute to the node and egde
    ip = {('client', 'r1'): {'ip1': 'fc00:1::2', 'ip2': 'fc00:1::1'}, 
        ('client','r3'): {'ip1': 'fc00:2::2', 'ip2': 'fc00:2::1'}, 
        ('r1','r2'): {'ip1': 'fc00:a::1', 'ip2': 'fc00:a::2'}, 
        ('r3','r4'): {'ip1': 'fc00:b::1', 'ip2': 'fc00:b::2'}, 
        ('r3','r5'): {'ip1': 'fc00:e::1', 'ip2': 'fc00:e::2'}, 
        ('r4','r5'): {'ip1': 'fc00:d::1', 'ip2': 'fc00:d::2'}, 
        ('r2','r5'): {'ip1': 'fc00:c::1', 'ip2': 'fc00:c::2'}, 
        ('r5','server'): {'ip1': 'fc00:3::1', 'ip2': 'fc00:3::2'}}
    nx.set_edge_attributes(G, ip)

    paths = list(nx.shortest_simple_paths(G, 'client', 'server', weight='weight'))
   
    lstName = []
    lstValue = []

    for path in paths[:2]:
        # print(path)
        lst = []
        for ip in range(len(path) - 1):
            lst.append(G[path[ip]][path[ip + 1]]['ip2'])
        # print(lst)
        lstValue.append(lst)
        lstName.append(path)
    
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
    nx.draw_networkx(G, pos, **options)

    # Set margins for the axes so that nodes aren't clipped
    ax = plt.gca()
    ax.margins(0.20)
    plt.axis("off")
    plt.savefig('mygraph.png')
    
    if num == 0:
        return lstValue 
    else:
        return lstName