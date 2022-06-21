# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 11:16:36 2022

@author: b8008458
"""


import geopandas as gpd
import pandana as pdna
import pandas as pd
import momepy 
import networkx as nx
import osmnx as ox

# import OD Matrix
ODMatrix = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\ODMatrix.gpkg")

# import network
network = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\network_SplitLineAtPoint.shp")

# import barriers
barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\RandomNodes.shp")

#%%

# clean ODMatrix 

# Remove any places with a total cost of 0

ODMatrix = ODMatrix[ODMatrix['total_cost'] != 0]

# Remove ODs where O = D

ODMatrix = ODMatrix[ODMatrix['origin_id'] != ODMatrix['destination_id']]


# Remove spare columns

ODMatrix.drop(['entry_cost', 'network_cost', 'exit_cost'], axis=1, inplace=True)




#%%

# plot network and points 
base = network.plot()


barriers.plot(ax=base, color='red')

#%%


network_G = momepy.gdf_to_nx(network, length="mm_len", multigraph=True)


#%%

network_SP = nx.shortest_path(network_G)

network_SP_len = nx.shortest_path_length(network_G)


#%%

nodes, edges = momepy.nx_to_gdf(
    momepy.gdf_to_nx(
        network.explode()
    )
)

nodes = nodes.set_index("nodeID")


#%%

for index, row in barriers.iterrows(): # barrierss is the GeoDataFrame that holds my points, read from a shapefile.
      barriers_xy = (barriers.geometry.y, barriers.geometry.x)
      barriers_node_id = ox.get_nearest_node(network_G, barriers_xy, method="euclidean") # returns ID of nearest node on my graph, graph_proj
      barriers_node_location = nodes.loc[barriers_node_id]
      barriers_node = tuple(barriers_node_location)
      network_G.add_node(barriers.xy)
      network_G.add_edge(barriers.xy, barriers_node)

