# libary imports
import momepy
import pandas as pd
import geopandas as gpd
import networkx as nx 
import osmnx as ox
from matplotlib import pyplot as plt
import pandana as pdna
import time
#%%

# start timer
start = time.time()
#%%

# read in edges
OSM_edges = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\BikeNetwork\bike_network_costs.shp')

#%%
# convert to network
G = momepy.gdf_to_nx(OSM_edges, approach="primal", length="cost")

#%%

# calculate betweeness_centrality
print("Starting calculation")

# use k = 500 for faster running
bc = nx.edge_betweenness_centrality(G, k = 20000, weight='cost', seed=23)
bc = pd.DataFrame(bc.items())

#%%

# join calculated betweeness and edges

OSM_edges['edge_index'] = range(1, len(OSM_edges) + 1)
OSM_edges['edge_index'] = OSM_edges['edge_index'] - 1
bc['edge_index'] =  range(1, len(bc) + 1)
bc['edge_index'] =  bc['edge_index'] - 1
OSM_edges = pd.merge(OSM_edges, bc, on = 'edge_index')


#%%

# rename columns and drop unnessacary rows
OSM_edges.rename(columns = {1:'Betweenness'}, inplace = True)
OSM_edges.drop([0,'edge_index'], axis=1, inplace=True)

#%%

OSM_edges.to_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\BikeNetwork\bike_network_costs_bc.shp')

#%%
end = time.time()

print("Execution time is:", end-start, "seconds")