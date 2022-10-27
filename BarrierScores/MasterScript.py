# Welcome to the barrier removal prioitisation tool! Minimal input should be required to this script, just set
# your working directory and the location that you're looking to analyse. Any issues please contact b8008458@newcastle.ac.uk

# set working directory. Add your own here:
working_directory = r"C:\Users\b8008458\Documents\2021_2022\BarrierScores"


# set study area. Areas must follow the naming structure used in OpenStreetMap.
# for example place = "York, United Kingdom" or place = "Pembrokeshire, United Kingdom"
place = "York, United Kingdom"


# no code beyond this point should require any input. Processing times will vary
# depending on the size of the area you are studying. 
# line 529 can be edited to significatly speed up the process


#########################################################################
# import packages
# an anaconda envrioment is required for this tool to be used. The lastest versions of
# OSMNx and pandana are also required. To install OSMNx use the following command in
# the anaconda prompt terminal: conda config --prepend channels conda-forge
# conda create -n ox --strict-channel-priority osmnx
# to install pandana simply type !pip install pandana into the python kernel
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

# clip NCN barriers and LSOAs to the study area
# load barriers
barriers = gpd.read_file(working_directory + "\Data\Barriers\Barriers_Auditing_v2.shp")

# load LSOA centeriods
lsoas = gpd.read_file(working_directory + "\Data\LSOAs\LSOAs.shp")

# load LSOA polygons with IMD Scores
imd_scores = gpd.read_file(working_directory + "\Data\LSOAs\IMD_Scores.shp")



# load the study area boundary
boundary = ox.geocode_to_gdf(place)
# convert to lsoas' crs
boundary = boundary.to_crs(lsoas.crs)
# convert to lsoas' crs
imd_scores = imd_scores.to_crs(lsoas.crs)
# convert to lsoas' crs
barriers = barriers.to_crs(lsoas.crs)
# clip the barriers to the study area
barriers = gpd.clip(barriers, boundary)
# reset barrier index position
barriers.reset_index(inplace = True)
# set crs
barriers = barriers.to_crs(4326)
# clip the LSOAs to the study area
lsoas = gpd.clip(lsoas, boundary)
imd_scores = gpd.clip(imd_scores, boundary)

# barriers are now loaded and clipped. Metrics can now be computed



# accessiablity metric
# this section computes the accessiablity improvement once a barrier is theorticaly removed, measured as a percentage
# both cycling and walking are considered as methods of transport
# the percentage improvement per barrier is stored
# accessiablity is measured as the number of amnities accessiable within a given walk or cycle distance

#######################################################################################################

# get location
walk_dist = 1200 # distance to be walked
no_pois = 1000 # max number of points to look for
type = 'walk'  # network type to get. walk, bike, all or drive

cities = ox.geocode_to_gdf([place])

# get all amenities for a given study area

tags = {"amenity": ["bar","cafe","pub","restaurant",
                    "college","kindergarten","library","school","university", "childcare",
                    "bicycle_parking","bicycle_repair_station","bicycle_rental","bus_station","ferry_terminal",
                    "taxi","atm","bank","bureau_de_change",
                    "clinic","dentist","doctors","hospital","pharmacy","social_facility","veterinary"
                    ,"arts_centre","cinema","community_centre","public_bookcase", "kitchen",
                    "social_centre", "theatre", "marketplace", "place_of_worship",
                    "police", "fire_station","post_box", "post_depot", "post_office", "townhall",
                    "drinking_water","toilets","water_point", "parcel_locker", "shower", "telephone",
                    "recycling"]}

pois = ox.geometries_from_place(place, tags)

# load streets from OSM
walk_graph = ox.graph_from_place(place, network_type = type) # download walking network


## clean data

# streets
walk_graph = ox.get_undirected(walk_graph) # cleans the network keeping parallel edges only if geometry is different
walk_graph = ox.projection.project_graph(walk_graph) # project graph
walk_streets = ox.graph_to_gdfs(walk_graph, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True) # convert graph to gdf
walk_streets = walk_streets[["geometry", "from", "to", "length"]] # clean columns
walk_streets = walk_streets.to_crs(27700) # set crs



# lsoas
lsoas = lsoas.reset_index(drop=True).explode().reset_index(drop=True) # clean
lsoas['lsoaID'] = range(0,len(lsoas)) # generate index column
lsoas = lsoas.set_index('lsoaID') # set index
lsoas = lsoas.to_crs(27700) # set crs


# pois

pois = pois.reset_index(drop=True).explode().reset_index(drop=True) # avoid multipart pois
pois['poiID'] = range(0,len(pois))
pois = pois.set_index('poiID')

# convert polygons to points
pois['geometry'] = pois.centroid

# clean columns
pois = pois[['geometry','amenity']]
pois = pois.to_crs(27700) # set crs


## generate pandana network
# nodes and edges for walk network
nodes_walk, edges_walk = momepy.nx_to_gdf( # convert network to gdf
    momepy.gdf_to_nx( # convert to nx graph
        walk_streets.explode() # remove multipart rows
    )
)
nodes_walk = nodes_walk.set_index('nodeID') # set index

# generate walk pandana network
walk_streets_pdna = pdna.Network( 
    nodes_walk.geometry.x,
    nodes_walk.geometry.y,
    edges_walk['node_start'], # set origins
    edges_walk['node_end'], # set destinations
    edges_walk[['mm_len']] # set edge length
)


# attach pois to the network
walk_streets_pdna.set_pois( # snap pois to network
    category = 'pois', # set name of the new layer snapped on the network
    maxdist = walk_dist, # set maximum distance
    maxitems = no_pois, # set maximum number of pois to look for
    x_col = pois.geometry.x,
    y_col = pois.geometry.y
)
results = walk_streets_pdna.nearest_pois( # calculate distances to pois
    distance = walk_dist, # maximum distance
    category = 'pois', # layer where we want to look for
    num_pois = no_pois, # max number of pois to look for
    include_poi_ids = True # include pois ids
)


# store results separately as distances and poiIDs

# separate distances from poi ids
distances = results.iloc[:,:round(len(results.columns)/2,)] # create df with distances
pois_ids = results.iloc[:,round(len(results.columns)/2,):] # create df with pois ids

# convert wide matrices to long
distances_long = pd.melt(distances.reset_index(), id_vars='nodeID',value_name='distance') # make matrix long
pois_ids_long = pd.melt(pois_ids.reset_index(), id_vars='nodeID',value_name='poiID') # make matrix long

# create an od long df containing nodeID, distance, and poiID
od = distances_long
od['poiID'] = pois_ids_long['poiID'].astype('Int64') # set a column with pois ids (as they are indexed, they are already in the right order)

# format od matrix and drop NAs
od = od[['nodeID','poiID','distance']] # clean columns
od = od.dropna() # drop NAs


# merge od data with POIs data
pois = pois.reset_index() # reset index pois df


od_pois_info = pd.merge(od, pois[['amenity','poiID']].reset_index(), left_on='poiID', right_on='poiID') # merge pois info to od matrix



# add lsoa information to the od_pois_info 
lsoa_nodes = walk_streets_pdna.get_node_ids( # get nearest street nodes to each postcode
    lsoas.geometry.x,
    lsoas.geometry.y
)
lsoa_nodes = gpd.GeoDataFrame(lsoa_nodes).reset_index() # reset index
lsoa_nodes = lsoa_nodes.rename(columns={'node_id':'nodeID'}) # change col names


# get lsoa geometries
lsoa_nodes = lsoa_nodes.merge(lsoas, on='lsoaID', how='left', suffixes=('','_y'))
lsoa_nodes.drop(lsoa_nodes.filter(regex='_y$').columns, axis =1, inplace=True)
lsoa_nodes = lsoa_nodes[['lsoaID','nodeID','geometry']]


# add lsoas to od_pois_info
od_pois_info = pd.merge(od_pois_info, lsoa_nodes, left_on='nodeID', right_on='nodeID') # add lsoa to od matrix


# save to geospatail format
od_pois_info = gpd.GeoDataFrame(od_pois_info, geometry = 'geometry')


# count the number of aminites accessable from a given lsoa
lsoa_level_accessablity = od_pois_info.groupby("lsoaID").size()


# convert to dataframe
lsoa_level_accessablity = pd.DataFrame(lsoa_level_accessablity)

# merge with orignal lsoa file
lsoas = lsoas.merge(lsoa_level_accessablity, on='lsoaID', how='left', suffixes=('','_y'))
lsoas.drop(lsoas.filter(regex='_y$').columns, axis =1, inplace=True)
lsoas.rename(columns = {0:'amenity count'}, inplace = True)



# Now repeat process with a broken network where edges with barriers on are removed
# create a network with edges with barriers on removed to simulate not being able to pass through a barrier
G = ox.graph_from_place(place, simplify=True, network_type=type)
G_edges = ox.graph_to_gdfs(ox.get_undirected(G), nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)
G_nodes = ox.graph_to_gdfs(ox.get_undirected(G), nodes=True, edges=False, node_geometry=True, fill_edge_geometry=False)
shply_line = G_edges.geometry.unary_union 
point = barriers.to_crs(G_edges.crs)
for i in range(len(point)):
    print(shply_line.interpolate(shply_line.project( point.geometry[i])).wkt) # snap points to line
result = point.copy()
result['geometry'] = result.apply(lambda row: shply_line.interpolate(shply_line.project( row.geometry)), axis=1)
buffer = result.geometry.buffer(0.00001) # create tiny buffer around points
broken_network = G_edges.intersects(buffer.unary_union)
broken_network = pd.DataFrame(broken_network)
broken_network.rename(columns = {0:'Clipped'}, inplace = True) # clip network
broken_network = pd.concat([broken_network,G_edges],axis=1)
# drop intersected lines
broken_network.drop(broken_network[broken_network['Clipped'] == True].index, inplace=True)
broken_network = broken_network[['geometry','to','from']]
broken_network = gpd.GeoDataFrame(broken_network, geometry='geometry')
G_edges = broken_network.to_crs(3857)
G_edges['length'] = G_edges.length
G_edges = G_edges.to_crs(4326)
G_edges = G_edges.to_crs(27700)



## clean data

# streets
walk_streets = G_edges[["geometry", "from", "to", "length"]] # clean columns
walk_streets = walk_streets.to_crs(27700) # set crs



## generate pandana network
# nodes and edges for walk network
nodes_walk, edges_walk = momepy.nx_to_gdf( # convert network to gdf
    momepy.gdf_to_nx( # convert to nx graph
        walk_streets.explode() # remove multipart rows
    )
)
nodes_walk = nodes_walk.set_index('nodeID') # set index

# generate walk pandana network
walk_streets_pdna = pdna.Network( 
    nodes_walk.geometry.x,
    nodes_walk.geometry.y,
    edges_walk['node_start'], # set origins
    edges_walk['node_end'], # set destinations
    edges_walk[['mm_len']] # set edge length
)


# attach pois to the network
walk_streets_pdna.set_pois( # snap pois to network
    category = 'pois', # set name of the new layer snapped on the network
    maxdist = walk_dist, # set maximum distance
    maxitems = no_pois, # set maximum number of pois to look for
    x_col = pois.geometry.x,
    y_col = pois.geometry.y
)
results = walk_streets_pdna.nearest_pois( # calculate distances to pois
    distance = walk_dist, # maximum distance
    category = 'pois', # layer where we want to look for
    num_pois = no_pois, # max number of pois to look for
    include_poi_ids = True # include pois ids
)


# store results separately as distances and poiIDs

# separate distances from poi ids
distances = results.iloc[:,:round(len(results.columns)/2,)] # create df with distances
pois_ids = results.iloc[:,round(len(results.columns)/2,):] # create df with pois ids

# convert wide matrices to long
distances_long = pd.melt(distances.reset_index(), id_vars='nodeID',value_name='distance') # make matrix long
pois_ids_long = pd.melt(pois_ids.reset_index(), id_vars='nodeID',value_name='poiID') # make matrix long

# create an od long df containing nodeID, distance, and poiID
od = distances_long
od['poiID'] = pois_ids_long['poiID'].astype('Int64') # set a column with pois ids (as they are indexed, they are already in the right order)

# format od matrix and drop NAs
od = od[['nodeID','poiID','distance']] # clean columns
od = od.dropna() # drop NAs


# merge od data with POIs data
pois = pois.reset_index() # reset index pois df



od_pois_info = pd.merge(od, pois[['amenity','poiID']].reset_index(), left_on='poiID', right_on='poiID') # merge pois info to od matrix



# add lsoa information to the od_pois_info 
lsoa_nodes = walk_streets_pdna.get_node_ids( # get nearest street nodes to each postcode
    lsoas.geometry.x,
    lsoas.geometry.y
)
lsoa_nodes = gpd.GeoDataFrame(lsoa_nodes).reset_index() # reset index
lsoa_nodes = lsoa_nodes.rename(columns={'node_id':'nodeID'}) # change col names


# get lsoa geometries
lsoa_nodes = lsoa_nodes.merge(lsoas, on='lsoaID', how='left', suffixes=('','_y'))
lsoa_nodes.drop(lsoa_nodes.filter(regex='_y$').columns, axis =1, inplace=True)
lsoa_nodes = lsoa_nodes[['lsoaID','nodeID','geometry']]



# add lsoas to od_pois_info
od_pois_info = pd.merge(od_pois_info, lsoa_nodes, left_on='nodeID', right_on='nodeID') # add lsoa to od matrix


# save to geospatail format
od_pois_info = gpd.GeoDataFrame(od_pois_info, geometry = 'geometry')



# count the number of aminites accessable from a given lsoa
lsoa_level_accessablity = od_pois_info.groupby("lsoaID").size()

# convert to dataframe
lsoa_level_accessablity = pd.DataFrame(lsoa_level_accessablity)

# merge with orignal lsoa file
lsoas = lsoas.merge(lsoa_level_accessablity, on='lsoaID', how='left', suffixes=('','_y'))
lsoas.drop(lsoas.filter(regex='_y$').columns, axis =1, inplace=True)
lsoas.rename(columns = {0:'amenity count barriers'}, inplace = True)

lsoas['amenity_diff'] =  lsoas['amenity count'].sub(lsoas['amenity count barriers'], axis = 0)
lsoas['amenity_diff_%'] = (lsoas['amenity count'] - lsoas['amenity count barriers']) / lsoas['amenity count'] * 100


# Calculate isochrones around each barrier


# function to get isochrones
def get_isochrone(
    lon, lat, walk_times=[15, 30], speed=4.5, name=None, point_index=None
):
    loc = (lat, lon)
    G = ox.graph_from_point(loc, simplify=True, network_type="all")
    gdf_nodes = ox.graph_to_gdfs(G, edges=False)
    center_node = ox.distance.nearest_nodes(G, lon, lat)
    #fig, ax = ox.plot_graph(G,node_color="w", node_size= 50)

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



# calculate isochrones

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



# plot isochrones on a map

import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=PendingDeprecationWarning)
ox.config(use_cache=True, log_console=False)
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

m = gdf.reset_index().explore(column="time", scheme="boxplot")
barriers.head(BARRIERS).explore(m=m, marker_kwds={"radius": 3, "color": "red"})


# remove shorter walk distances
isochrones = isochrones[isochrones.time == 15]
isochrones['point_index'] = isochrones['point_index'].fillna(0)
isochrones.head(10)


# check crs of isochrones
isochrones.crs
# set crs to match isochrones
lsoas = lsoas.to_crs(4326)
lsoas.crs



# join lsoas to isochrones
left_join = lsoas.sjoin(isochrones, how = "left")
barrier_score = left_join.groupby("name").mean("amenity_diff_%") # calculate accessiablity score per barrier
barrier_score = barrier_score[['objectid', 'amenity_diff_%']]
barriers_join = barriers.merge(barrier_score, left_on = 'globalid', right_on = 'name', how='left') # join datafranes
barriers_join['amenity_diff_%'] = barriers_join['amenity_diff_%'].fillna(0) # fill nans with 0
barriers_walkscore = barriers_join


######################################################################################
# calcualte network metrics
bike_graph = ox.graph_from_place(place, network_type="all",clean_periphery=True)
edges = ox.graph_to_gdfs(ox.get_undirected(bike_graph), nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)
edges.drop(["ref","name","maxspeed","lanes","service","bridge","tunnel","access","junction","width","est_width", "osmid"], axis=1, inplace=True)
edges['highway'] = edges['highway'].str.replace("'"," ")
edges['cost'] = edges['length']

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

# read in edges
OSM_edges = edges
# convert to graph
G = momepy.gdf_to_nx(OSM_edges, approach="primal", length="cost")

# calculate betweeness_centrality
print("Starting calculation")
print("This can take up to 24 hours to process depending on graph size and processing power...")
# use k = 1000 for faster running
bc = nx.edge_betweenness_centrality(G, weight='cost', seed=23, normalized = False)
bc = pd.DataFrame(bc.items())
print("Betweenness calculated")


# join calculated betweeness and edges
OSM_edges['edge_index'] = range(1, len(OSM_edges) + 1)
OSM_edges['edge_index'] = OSM_edges['edge_index'] - 1
bc['edge_index'] =  range(1, len(bc) + 1)
bc['edge_index'] =  bc['edge_index'] - 1
OSM_edges = pd.merge(OSM_edges, bc, on = 'edge_index')

# rename columns and drop unnessacary rows
OSM_edges.rename(columns = {1:'Betweenness'}, inplace = True)
OSM_edges.drop([0,'edge_index'], axis=1, inplace=True)
OSM_edges = OSM_edges.to_crs(27700)


######################################################################################
# with metrics calculated, and overall score can now be determined per barrier
# reset barrier crs
barriers_walkscore = barriers_walkscore.to_crs(27700)
# get list of current column headers
barriers_columnlist = list(barriers_walkscore)
# join IMD rank to barrier
join_left_df = barriers_walkscore.sjoin(imd_scores, how="left")
barriers_columnlist += ['IMD_Score'] 
barriers_walkscore = join_left_df[barriers_columnlist]
# join betweeness to barrier
join_left_df = barriers_walkscore.sjoin_nearest(OSM_edges, how="left")
barriers_columnlist += ['Betweenness']
barriers_walkscore = join_left_df[barriers_columnlist]

# normliase all mertic
barrier_copy = barriers_walkscore[['Betweenness','Critical_1', 'IMD_Score','amenity_diff_%']] 
# inverse weighting for barriers as wider barriers are better barriers :)
barrier_copy['Critical_1'] *= -1
barrier_copy['IMD_Score'] = barrier_copy['IMD_Score'].astype(int)
for column in barrier_copy:
    barrier_copy[column] = (barrier_copy[column] - barrier_copy[column].min()) / (barrier_copy[column].max() - barrier_copy[column].min())


# apply weights derived from AHP
barrier_copy['Betweenness'] = barrier_copy['Betweenness'] * 0.064
barrier_copy['Critical_width_score'] = barrier_copy['Critical_1'] * 0.451
barrier_copy['IMD_Score'] = barrier_copy['IMD_Score'] * 0.093 
barrier_copy['amenity_diff_%'] = barrier_copy['amenity_diff_%'] * 0.359


# final scoring
cols = ['Betweenness','Critical_width_score','IMD_Score', 'amenity_diff_%'] 
barrier_copy['Overall_Score'] = barrier_copy[cols].sum(axis=1)


# join final scores back to original barrier dataset
# set indexs to join on
barrier_copy['Index'] = barrier_copy.index
barriers['Index'] = barriers.index

# join 
barrier_copy = gpd.GeoDataFrame(barrier_copy)
join = barriers.merge(barrier_copy, on = 'Index', how='left', suffixes=('_x', ''))
join.drop(join.filter(regex='_x$').columns, axis=1, inplace=True)
join.drop(join.columns[[0]], axis = 1, inplace=True)
join.drop(['IMD_Score','amenity_diff_%', 'Index', 'Betweenness', 'Critical_width_score'], axis=1, inplace=True)
join.drop(['Critical_1'], axis=1, inplace=True)
join = barriers.merge(join, on = 'geometry', how='left', suffixes=('_x', ''))
join.drop(join.filter(regex='_x$').columns, axis=1, inplace=True)
join.drop(['Index','index'], axis = 1, inplace=True)
join[['Count_Atta','PhotoURL','Tranch4','Redesigned','SlopeNote','Compliant2','Compliant','AttachID','CountAttac','Photo2','Photo1','AuditAme_1','Date1', 'Date2','Date3','Restrict_1','CommentsBe','CommentsAf','Editor','EditDate','Creator','CreationDa','Status','Other','Restrictio','OnNCN','AuditAmend','globalid']] = join[['Count_Atta','PhotoURL','Tranch4','Redesigned','SlopeNote','Compliant2','Compliant','AttachID','CountAttac','Photo2','Photo1','AuditAme_1','Date1', 'Date2','Date3','Restrict_1','CommentsBe','CommentsAf','Editor','EditDate','Creator','CreationDa','Status','Other','Restrictio','OnNCN','AuditAmend','globalid']].astype(str)

# output to file
join.to_file(working_directory + "\Outputs\scoredbarriers.shp")


