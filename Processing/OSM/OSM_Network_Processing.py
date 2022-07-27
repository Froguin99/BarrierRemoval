# libary imports
import momepy
import pandas as pd
import geopandas as gpd
import networkx as nx 
import osmnx as ox
from matplotlib import pyplot as plt

#%%
bike_graph = ox.graph_from_place('York, United Kingdom', network_type="all",clean_periphery=True)

#%%

#%%

ox.save_graph_geopackage(bike_graph, filepath=(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Bike Network\bike_network.shp'))

#%%
#edges = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\BikeNetwork\bike_network.shp')

edges = ox.graph_to_gdfs(ox.get_undirected(bike_graph), nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)
edges.drop(["ref","name","maxspeed","lanes","service","bridge","tunnel","access","junction","width","est_width", "osmid"], axis=1, inplace=True)
edges['highway'] = edges['highway'].str.replace("'"," ")

#%%
edges['cost'] = edges['length']

#%%

# weight edges
edges.loc[edges['highway']== "cycleway", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "bridleway", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "living_street", 'cost'] = edges['cost'] * 0.6
edges.loc[edges['highway']== "path", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "pedestrian", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'bridleway','service\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'cycleway','path\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'cycleway','track\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'cycleway','unclassified\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'living_street','pedestrian\']", 'cost'] = edges['cost'] * 0.6
edges.loc[edges['highway']== "[\'living_street','service\']", 'cost'] = edges['cost'] * 0.6
edges.loc[edges['highway']== "[\'residential','bridleway\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','cycleway\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','path\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','living_street\']", 'cost'] = edges['cost'] * 0.6
edges.loc[edges['highway']== "[\'residential','path\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','pedestrian\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','service\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','track','path\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','track\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'residential','unclassified\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'service','cycleway\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'service','path\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'service','pedestrian\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'service','track\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'service','unclassified\']", 'cost'] = edges['cost'] * 0.4
edges.loc[edges['highway']== "[\'service','cycleway\']", 'cost'] = edges['cost'] * 0.4

# increase weights on unuseable roads
edges.loc[edges['highway']== "trunk", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "trunk_link", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "service", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "primary", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "secondary", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "tertiary", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "unclassified", 'cost'] = edges['cost'] * 10
edges.loc[edges['highway']== "motorway", 'cost'] = edges['cost'] * 100
edges.loc[edges['highway']== "motorway_link", 'cost'] = edges['cost'] * 100




#%%

edges.to_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Bike Network\bike_network_costs.shp')



