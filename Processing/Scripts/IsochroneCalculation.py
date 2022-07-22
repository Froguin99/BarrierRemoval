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
from shapely.geometry import Point

#%%

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=PendingDeprecationWarning)
ox.config(use_cache=True, log_console=False)

#%%
# get some cities
cities = ["Newcastle"]  # ["Hereford", "Worcester", "Gloucester"]
cities = ox.geocode_to_gdf([{"city": c, "country": "UK"} for c in cities])

# get some schools
tags = {"amenity": "school"}
schools = pd.concat(
    [
        ox.geometries.geometries_from_polygon(r["geometry"], tags)
        for i, r in cities.iterrows()
    ]
)
#schools = (
    #schools.loc["ways"].dropna(axis=1, thresh=len(schools) / 4).drop(columns=["nodes"])
#)
# change polygon to point
schools["geometry"] = schools.centroid

#%%

# function to get isochrones
def get_isochrone(
    lon, lat, walk_times=[15, 30], speed=4.5, name=None, point_index=None
):
    loc = (lat, lon)
    G = ox.graph_from_point(loc, simplify=True, network_type="walk")
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
SCHOOLS = 5

# build geopandas data frame of isochrone polygons for each school
isochrones = pd.concat(
    [
        gpd.GeoDataFrame(
            get_isochrone(
                r["geometry"].x,
                r["geometry"].y,
                name=r["name"],
                point_index=i,
                walk_times=WT,
            ),
            crs=schools.crs,
        )
        for i, r in schools.head(SCHOOLS).iterrows()
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
schools.head(SCHOOLS).explore(m=m, marker_kwds={"radius": 3, "color": "red"})
