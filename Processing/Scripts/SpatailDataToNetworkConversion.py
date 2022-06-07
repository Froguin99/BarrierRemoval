# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 10:25:40 2022

@author: b8008458
"""
#%%
# Standard imports
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import geopandas as gpd
import momepy 
import networkx as nx
import pandana as pdna
from mapclassify import greedy
import matplotlib.pyplot as plt

#%%

# Import barriers 

barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\FullBarrierLayer.shp")


# Import network

network_edges = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\NetworkTesting\NCNReprojectedAndCleanedClip.shp")

#%%

# plot network
f, ax = plt.subplots(figsize=(10, 10))
network_edges.plot(ax=ax)
ax.set_axis_off()
plt.show()


#%%

nodes, edges = momepy.nx_to_gdf(momepy.gdf_to_nx(network_edges.explode()))
nodes = nodes.set_index("nodeID")


#%%
# plot network
f, ax = plt.subplots(figsize=(10, 10))
edges.plot(ax=ax)
ax.set_axis_off()
plt.show()

#%%
network_edges.plot(greedy(network_edges), categorical=True, figsize=(10, 10), cmap="Set3").set_axis_off()


#%%
graph = momepy.gdf_to_nx(edges, approach='primal', length='mm_len')


#%%
nx.draw(graph, node_size=100)
print("This graph was drawn using network x's plotting function, and will come out as a random shape every time")

#%%
f, ax = plt.subplots(figsize=(10, 10))
nodes.plot(ax=ax, zorder=2, label="network nodes")
barriers.plot(ax=ax, zorder=3, label="Barriers")
edges.plot(ax=ax, zorder=1)
ax.set_axis_off()
plt.legend(loc="upper left")
plt.show()


#%%
f, ax = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
network_edges.plot(color='#e32e00', ax=ax[0])
for i, facet in enumerate(ax):
    facet.set_title(("NCN", "Primal graph", "Overlay")[i])
    facet.axis("off")
nx.draw(graph, {n:[n[0], n[1]] for n in list(graph.nodes)}, ax=ax[1], node_size=15)
network_edges.plot(color='#e32e00', ax=ax[2], zorder=-1)
nx.draw(graph, {n:[n[0], n[1]] for n in list(graph.nodes)}, ax=ax[2], node_size=15)

#%%
graph = momepy.node_degree(graph, name='degree')


#%%

net = pdna.Network(nodes.geometry.x, nodes.geometry.y, edges["node_start"], edges["node_end"], edges[["Shape_Leng"]])

#%%

barriers_reversed = barriers.iloc[::-1].reset_index()


#%%

origins = net.get_node_ids(barriers.geometry.x, barriers.geometry.y).values
destinations = net.get_node_ids(barriers_reversed.geometry.x, barriers_reversed.geometry.y).values


origins_df = pd.DataFrame(origins)
destinations_df = pd.DataFrame(destinations)

#%%

routes = []

net.shortest_paths(origins, destinations)


#%%
barriers_shortest_paths = net.shortest_paths(barriers, barriers)