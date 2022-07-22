# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 16:47:22 2022

@author: b8008458
"""
# import packages
import geopandas as gpd
import osmnx as ox
import momepy
import pandana as pdna
import pandas as pd
import numpy as np
import networkx as nx

from scipy.spatial import cKDTree
from shapely.geometry import Point

from shapely.geometry import box

#%%

# get all amenities for a given study area
place = "Newcastle Upon Tyne, United Kingdom"
tags = {"amenity": ["cafe","bar","pub","restaurant",
                    "college","kindergarten","language_school","library","toy_library","music_school","school","university"
                    ,"bicycle_parking","bicycle_repair_station","bicycle_rental","bus_station","car_rental","car_sharing","car_wash","fuel","ferry_terminal",
                    "taxi","atm","bank","bureau_de_change",
                    "clinic","dentist","doctors","hospital","pharmacy","social_facility","veterinary"
                    ,"arts_centre","cinema","community_centre","conference_centre","events_venue","foutain","nightclub","public_bookcase",
                    "social_centre", "theatre", 
                    "police", "fire_station", "post_box", "post_depot", "post_office", "ranger_station", "townhall",
                    "bbq","drinking_water","give_box","parcel_locker","shelter","shower","telephone","toilets","water_point",
                    "recycling","waste_transfer_station",
                    "childcare","internet_cafe","kitchen","marketplace","place_of_worship","public_bath"]}

pois = ox.geometries_from_place(place, tags)
pois = pois[['osmid', 'geometry','amenity']]

# get bikeable network and NCN Barriers
# bike_graph = ox.graph_from_place(place, network_type = 'all')
bike_graph = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\BikeNetwork\bike_network_costs.shp')
barriers = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\FullBarrierLayer.shp')

#%%

# pre-process points of interest
pois = pois.reset_index(drop=True).explode().reset_index(drop=True) # avoid multipart pois
pois['poiID'] = range(0,len(pois))
pois = pois.set_index('poiID')

# convert polygons to points
pois['geometry'] = pois.centroid







#%%


G = momepy.gdf_to_nx(bike_graph)

# find the centermost node and then project the graph to UTM
gdf_nodes = ox.graph_to_gdfs(G, edges=False)
x, y = gdf_nodes['geometry'].unary_union.centroid.xy
center_node = ox.get_nearest_node(G, (y[0], x[0]))
G = ox.project_graph(G)


trip_times = [5, 10, 15, 20, 25] # in minutes
travel_speed = 4.5 # walking speed in km/hour

# add an edge attribute for time in minutes required to traverse each edge
meters_per_minute = travel_speed * 1000 / 60 # km per hour to m per minute
for u, v, k, data in G.edges(data=True, keys=True):
    data['time'] = data['length'] / meters_per_minute



# get one color for each isochrone
iso_colors = ox.plot.get_colors(n=len(trip_times), cmap='plasma', start=0, return_hex=True)


# color the nodes according to isochrone then plot the street network
node_colors = {}
for trip_time, color in zip(sorted(trip_times, reverse=True), iso_colors):
    subgraph = nx.ego_graph(G, center_node, radius=trip_time, distance='time')
    for node in subgraph.nodes():
        node_colors[node] = color
nc = [node_colors[node] if node in node_colors else 'none' for node in G.nodes()]
ns = [15 if node in node_colors else 0 for node in G.nodes()]
fig, ax = ox.plot_graph(G, node_color=nc, node_size=ns, node_alpha=0.8, node_zorder=2,
                        bgcolor='k', edge_linewidth=0.2, edge_color='#999999')


#%%

# make the isochrone polygons
isochrone_polys = []
for trip_time in sorted(trip_times, reverse=True):
    subgraph = nx.ego_graph(G, center_node, radius=trip_time, distance='time')
    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
    isochrone_polys.append(bounding_poly)
    


# plot the network then add isochrones as colored descartes polygon patches
fig, ax = ox.plot_graph(G, show=False, close=False, edge_color='#999999', edge_alpha=0.2,
                        node_size=0, bgcolor='k')
for polygon, fc in zip(isochrone_polys, iso_colors):
    patch = PolygonPatch(polygon, fc=fc, ec='none', alpha=0.6, zorder=-1)
    ax.add_patch(patch)
plt.show()




#%%

# create pandana network
nodes, edges = momepy.nx_to_gdf(momepy.gdf_to_nx(bike_graph.explode()))
nodes = nodes.set_index("nodeID")
edges_pdna = pdna.Network(nodes.geometry.x, nodes.geometry.y, edges['node_start'], edges['node_end'], edges[['cost']])


#%%

# attach points of interest to the pandana network

edges_pdna.set_pois(category = 'pois', maxdist = 5000 # 5km distance, change depending on if looking for walking or cycling,
                    ,maxitems = 700 # number of ameinites to find
                    ,x_col = pois.geometry.x
                    ,y_col = pois.geometry.y)


# calculate distance to points of interest
results = edges_pdna.nearest_pois(distance = 5000, category = 'pois', num_pois = 700, include_poi_ids = True)


#%%




