# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 17:29:48 2022

@author: b8008458
"""
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 12:27:23 2022

@author: b8008458
"""

import pandas as pd
import warnings
import networkx as nx
import geopandas as gpd
import osmnx as ox
from shapely.ops import split
import momepy
from shapely.geometry import Point

#%%


warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=PendingDeprecationWarning)
ox.config(use_cache=True, log_console=False)
#%%

place = "York, United Kingdom"
# get location
cities = ox.geocode_to_gdf([place])

# get all amenities for a given study area

tags = {"amenity": ["cafe","pub","restaurant",
                    "college","kindergarten","library","school","university"
                    ,"bicycle_parking","bicycle_repair_station","bicycle_rental","bus_station","ferry_terminal",
                    "taxi","atm","bank","bureau_de_change",
                    "clinic","dentist","doctors","hospital","pharmacy","social_facility","veterinary"
                    ,"arts_centre","cinema","community_centre","public_bookcase",
                    "social_centre", "theatre", 
                    "police", "fire_station", "post_office", "townhall",
                    "drinking_water","toilets","water_point",
                    "recycling"]}

pois = ox.geometries_from_place(place, tags)



# get some barriers
barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Barriers\YorkBarriers.shp")


# get population weighted centroids
pwc = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Centriods\YorkLSOAsSinglePartGPKG.gpkg")

# pre-process points of interest
pois = pois.reset_index(drop=True).explode().reset_index(drop=True) # avoid multipart pois
pois['poiID'] = range(0,len(pois))
pois = pois.set_index('poiID')

# convert polygons to points
pois['geometry'] = pois.centroid

# clean columns
pois = pois[['geometry','amenity']]


# function to get isochrones
def get_isochrone(
    lon, lat, walk_times=[15, 30], speed=4.5, name=None, point_index=None
):
    loc = (lat, lon)
    G = ox.graph_from_point(loc, simplify=True, network_type="all")
    gdf_nodes = ox.graph_to_gdfs(G, edges=False)
    center_node = ox.distance.nearest_nodes(G, lon, lat)

    meters_per_minute = speed * 1000 / 60  # km per hour to m per minute
    for u, v, k, data in G.edges(data=True, keys=True):
        data["time"] = data["length"] / meters_per_minute
    polys = []
    for walk_time in walk_times:
        subgraph = nx.ego_graph(G, center_node, radius=walk_time, distance="time")
        node_points = [
            Point(data["x"], data["y"]) for node, data in subgraph.nodes(data=True)
        ]
        polys.append(gpd.GeoSeries(node_points).unary_union.convex_hull)
    info = {}
    if name:
        info["name"] = [name for t in walk_times]
    if point_index:
        info["point_index"] = [point_index for t in walk_times]
    return {**{"geometry": polys, "time": walk_times}, **info}



#%%

WT = [5, 10, 15]
BARRIERS = len(barriers)

# build geopandas data frame of isochrone polygons for each barrier
isochrones = pd.concat(
    [
        gpd.GeoDataFrame(
            get_isochrone(
                r["geometry"].x,
                r["geometry"].y,
                name=r["globalid"],
                point_index=i,
                walk_times=WT,
            ),
            crs=barriers.crs,
        )
        for i, r in barriers.head(BARRIERS).iterrows()
    ]
)



#%%

warnings.filterwarnings("ignore")

gdf = isochrones.set_index(["time", "point_index"]).copy()
# remove shorter walk time from longer walk time polygon to make folium work better
for idx in range(len(WT)-1,0,-1):
    gdf.loc[WT[idx], "geometry"] = (
        gdf.loc[WT[idx]]
        .apply(
            lambda r: r["geometry"].symmetric_difference(
                gdf.loc[(WT[idx-1], r.name), "geometry"]
            ),
            axis=1,
        )
        .values
    )

m = gdf.reset_index().explore(column="time", height=300, width=500, scheme="boxplot")
barriers.head(BARRIERS).explore(m=m, marker_kwds={"radius": 3, "color": "red"})
#%%

# remove shorter walk distances
isochrones = isochrones[isochrones.time == 15]
isochrones['point_index'] = isochrones['point_index'].fillna(0)
isochrones.head(10)
join_inner_df = pois.sjoin(isochrones, how='inner')
result = join_inner_df.groupby('name').size()

#%%
# function to get isochrones
def get_isochrone(
    lon, lat, walk_times=[15, 30], speed=4.5, name=None, point_index=None
):
    loc = (lat, lon)
    G = ox.graph_from_point(loc, simplify=True, network_type="all")
    # disconnect network at barriers
    G = momepy.nx_to_gdf(G)
    
    G = split(G, loc)
    G = momepy.gdf_to_nx(G)
    gdf_nodes = ox.graph_to_gdfs(G, edges=False)
    center_node = ox.distance.nearest_nodes(G, lon, lat)

    meters_per_minute = speed * 1000 / 60  # km per hour to m per minute
    for u, v, k, data in G.edges(data=True, keys=True):
        data["time"] = data["length"] / meters_per_minute
    polys = []
    for walk_time in walk_times:
        subgraph = nx.ego_graph(G, center_node, radius=walk_time, distance="time")
        node_points = [
            Point(data["x"], data["y"]) for node, data in subgraph.nodes(data=True)
        ]
        polys.append(gpd.GeoSeries(node_points).unary_union.convex_hull)
    info = {}
    if name:
        info["name"] = [name for t in walk_times]
    if point_index:
        info["point_index"] = [point_index for t in walk_times]
    return {**{"geometry": polys, "time": walk_times}, **info}
#%%

WT = [5, 10, 15]
BARRIERS = len(barriers)

# build geopandas data frame of isochrone polygons for each barrier
isochrones = pd.concat(
    [
        gpd.GeoDataFrame(
            get_isochrone(
                r["geometry"].x,
                r["geometry"].y,
                name=r["globalid"],
                point_index=i,
                walk_times=WT,
            ),
            crs=barriers.crs,
        )
        for i, r in barriers.head(BARRIERS).iterrows()
    ]
)

