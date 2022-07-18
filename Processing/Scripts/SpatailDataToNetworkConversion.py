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
from shapely.ops import split

#%%

# Import barriers 


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\FullBarrierLayer.shp
barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersSinglePart.shp")


# Import network


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\NCNReprojectedAndCleanedClip.shp
network_edges = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\RebuildingNetwork\NCNNewcastleSplitShpLess.shp")


# Import OD Matrix from QGIS


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\ODMatrix.shp
QGIS_OD_Matrix = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\ODMatrix.shp")




#%%

# plot network
f, ax = plt.subplots(figsize=(10, 10))
network_edges.plot(ax=ax)
ax.set_axis_off()
plt.show()


#%%

# convert shapefile to nodes and edges

nodes, edges = momepy.nx_to_gdf(momepy.gdf_to_nx(network_edges.explode()))
nodes = nodes.set_index("nodeID")

#%%



# snap barriers to lines

shply_line = edges.geometry.unary_union


for i in range(len(barriers)):
    print(shply_line.interpolate(shply_line.project( barriers.geometry[i])).wkt)


result = barriers.copy()
result['geometry'] = result.apply(lambda row: shply_line.interpolate(shply_line.project( row.geometry)), axis=1)
print(result)


#%%

#%%
# plot network
f, ax = plt.subplots(figsize=(10, 10))
edges.plot(ax=ax)
ax.set_axis_off()
plt.show()

#%%

# check for poor topology
#network_edges.plot(greedy(network_edges), categorical=True, figsize=(10, 10), cmap="Set3").set_axis_off()


#%%

# convert to graph 
graph = momepy.gdf_to_nx(edges, approach='primal', length='Shape_leng')


#%%

# plot network as a graph 
#nx.draw(graph, node_size=100)
#print("This graph was drawn using network x's plotting function, and will come out as a random shape every time")

#%%

# plot barriers on network
f, ax = plt.subplots(figsize=(10, 10))
nodes.plot(ax=ax, zorder=2, label="network nodes")
barriers.plot(ax=ax, zorder=3, label="Barriers")
edges.plot(ax=ax, zorder=1)
ax.set_axis_off()
plt.legend(loc="upper left")
plt.show()


#%%

# plot network, graph and overlayed
f, ax = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
network_edges.plot(color='#e32e00', ax=ax[0])
for i, facet in enumerate(ax):
    facet.set_title(("Geographic network", "Primal graph", "Overlay")[i])
    facet.axis("off")
nx.draw(graph, {n:[n[0], n[1]] for n in list(graph.nodes)}, ax=ax[1], node_size=15)
network_edges.plot(color='#e32e00', ax=ax[2], zorder=-1)
nx.draw(graph, {n:[n[0], n[1]] for n in list(graph.nodes)}, ax=ax[2], node_size=15)

#%%

# calculate node degree
# graph = momepy.node_degree(graph, name='degree')


#%%

# convert to pandana network
net = pdna.Network(nodes.geometry.x, nodes.geometry.y, edges["node_start"], edges["node_end"], edges[["Shape_Leng"]])

#%%

# create a reversed list of barriers in order to make a OD list
barriers_reversed = barriers.iloc[::-1].reset_index()


#%%

# set origins and destinataions
origins = net.get_node_ids(barriers.geometry.x, barriers.geometry.y).values
destinations = net.get_node_ids(barriers_reversed.geometry.x, barriers_reversed.geometry.y).values


origins_df = pd.DataFrame(origins)
destinations_df = pd.DataFrame(destinations)

#%%

# import itertools package
# create list of all combinations
import itertools
OD_pairs = list(itertools.product(origins,destinations))

# split into two dataframes
OD_pairs_df = pd.DataFrame(OD_pairs, columns =['Origins', 'Destinations'])
OD_Origins = OD_pairs_df['Origins']
OD_Destinations = OD_pairs_df['Destinations']
OD_Origins_Arrary = OD_Origins.to_numpy()
OD_Destinations_Arrary = OD_Destinations.to_numpy()

#%%

# remove i - i and j - j 
QGIS_OD_Matrix = QGIS_OD_Matrix[QGIS_OD_Matrix['origin_id'] != QGIS_OD_Matrix['destinatio']]
OD_pairs_df['origin_id'] = QGIS_OD_Matrix['origin_id']
OD_pairs_df = OD_pairs_df.dropna()
OD_pairs_df.drop('origin_id', axis=1, inplace=True)

#%%

print("Starting route finding section...")
# find all routes and all route distances 
routes = []
distances = []

for a,b in OD_pairs:
    route = net.shortest_paths(OD_Origins_Arrary,OD_Destinations_Arrary)
    routes.append(route)


print("...Finished route finding")
#%%

route_df = pd.DataFrame({'Routes':route})


OD_Route_df = route_df.join(OD_pairs_df)


#%%

joined_OD_Matrix = QGIS_OD_Matrix.join(OD_Route_df)
joined_OD_Matrix = joined_OD_Matrix[joined_OD_Matrix.total_cost !=0]
joined_OD_Matrix['routes_string'] = joined_OD_Matrix['Routes'].agg(lambda x: ','.join(map(str, x)))


#%%


# ALL CODE BEYOND THIS POINT IS STILL VERY MUCH A WORK IN PROGRESS
#joined_OD_Matrix['total_cost'] = joined_OD_Matrix['total_cost'] * 10000


#%%

joined_OD_Matrix['pairs'] = joined_OD_Matrix['Origins'].astype(str) + joined_OD_Matrix['Destinations'].astype(str)
min_network_distances_df = joined_OD_Matrix.groupby(['pairs', 'origin_id'])['total_cost'].min()

#%%

# remove rows with the same start and end which aren't minium network distance
joined_OD_Matrix = pd.merge(min_network_distances_df, joined_OD_Matrix,how = 'outer', on = 'pairs')
joined_OD_Matrix = joined_OD_Matrix[joined_OD_Matrix['total_cost_x'] == joined_OD_Matrix['total_cost_y']]




#%%

# export to find closest node to barrier in QGIS (to hard to do in python!) 

# result['Nearest_Node'] = np.nan
# nodes.to_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\NetworkTesting\nodes.shp")
# result.to_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\NetworkTesting\result.shp")

# # use v.distance (reults to nodes, upload = to_att on column Node_no)

# #%%

# # bring results back in 

# result = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\NetworkTesting\resultnodes.shp')

# #%%

# # clean dataframes

# nodes['source'] = 'network'

# result['source'] = 'barriers'

# result = result.filter(['geometry','source','Nearest_No'])





# #%%

barrier_net = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\SnapGeomToLayer\net_split_at_points.shp")

barriernodes, barrieredges = momepy.nx_to_gdf(momepy.gdf_to_nx(barrier_net.explode()))
barriergraph = momepy.gdf_to_nx(barrieredges, approach='primal')
positions = {n: [n[0], n[1]] for n in list(barriergraph.nodes)}



#%%
print ("finding neighbors ....")
indx_neighbors = {}
for node in barriergraph.nodes():
    indx_neighbors.setdefault(node,[]).extend(list(nx.all_neighbors(barriergraph,node)))

neighbors_df = pd.DataFrame(list(indx_neighbors.items()), columns = ['Start_node','Neighbors'])
neighbors_df['index'] = neighbors_df.index
barriers['index'] = barriers.index
barriers = pd.merge(barriers, neighbors_df)
 
#%%


# use test = nx.neighbors(graph, (-2.027785157596724,55.08273981982428))
# list(test)
# in order to access neighbours


#graph.add_nodes_from(result.index)
#graph.add_nodes_from(nodes.index)
#%%

Hubdistance = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\NetworkWithHubDistance\NCNHUBDISTANCE.shp")


