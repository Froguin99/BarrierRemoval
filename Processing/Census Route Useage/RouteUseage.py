# libary imports
import momepy
import pandas as pd
import geopandas as gpd
import networkx as nx 
import osmnx as ox
from matplotlib import pyplot as plt
import pandana as pdna
import time
import numpy as np


#%%

# start timer
start = time.time()
#%%

# read in edges
OSM_edges = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Bike Network\bike_network_costs.shp')


# read in population weighted centeroids
pwc = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Centriods\YorkLSOAsReproSingle.gpkg')
#%%

# rename column headers
pwc.rename(columns = {'WF01BEW1447053441690848Cleaned_field_1':'LSOA Name'}, inplace=True)
#%%

# convert shapefile to nodes and edges

nodes, edges = momepy.nx_to_gdf(momepy.gdf_to_nx(OSM_edges.explode()))
nodes = nodes.set_index("nodeID")
#%%

edges_pdna = pdna.Network(nodes.geometry.x, nodes.geometry.y, edges['node_start'], edges['node_end'], edges[['cost']])
#%%

# create a reversed list of population weighted centeroids in order to make a OD list
pwc_reversed = pwc.iloc[::-1].reset_index()
#%%

# set origins and destinataions
origins = edges_pdna.get_node_ids(pwc.geometry.x, pwc.geometry.y).values
destinations = edges_pdna.get_node_ids(pwc_reversed.geometry.x, pwc_reversed.geometry.y).values
origins_df = pd.DataFrame(origins)
destinations_df = pd.DataFrame(destinations)
#%%

# create a copy of origins dataframe to allow for joining on index later
origins_df['origins_index'] = range(1, len(origins) + 1)
origins_df['origins_index'] = origins_df['origins_index'] - 1
origins_index_df = origins_df
origins_index_df.rename(columns = {0:'Origins'}, inplace = True)

# add column of index positions to pwc for index join later
pwc['origins_index'] = range(1, len(pwc) + 1)
pwc['origins_index'] = pwc['origins_index'] - 1
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

OD_pairs_df = pd.merge(OD_pairs_df, origins_index_df, on='Origins', how='outer')
OD_pairs_pwc_join = OD_pairs_df.merge(pwc)
#%%

# find number of columns in dataframe
dataframe_width = OD_pairs_pwc_join.shape[1]

# remove rows from the dataframe where no trips are present

startPos = 8
row_num = 1
# counter = 0 

for startID in OD_pairs_pwc_join['Origins']:
    if OD_pairs_pwc_join.iloc[row_num,startPos] == '0':
        OD_pairs_pwc_join.at[row_num,'flag'] = 'True'
        OD_pairs_pwc_join.at[row_num,'trips'] = OD_pairs_pwc_join.iloc[row_num,startPos]
        row_num = row_num + 1
        startPos = startPos + 1
    else:
        OD_pairs_pwc_join.at[row_num,'flag'] = 'False'
        OD_pairs_pwc_join.at[row_num,'trips'] = OD_pairs_pwc_join.iloc[row_num,startPos]
        row_num = row_num + 1
        startPos = startPos + 1
    if startPos == (OD_pairs_pwc_join.shape[1]) - 3:
        startPos = 8
    if row_num == (OD_pairs_pwc_join.shape[0]) - 1:
        row_num = 0
#%%

# drop rows where the flag is true
OD_pairs_pwc_join.drop(OD_pairs_pwc_join[OD_pairs_pwc_join['flag'] == 'True'].index, inplace=True) 

#%%

# edit to .iloc[0:1000] to make smaller data
sample_df = OD_pairs_pwc_join
   

#%%

# duplicate rows based on the number of trips made
sample_df = sample_df.dropna(axis=0)
sample_df = sample_df.loc[sample_df.index.repeat(sample_df['trips'])]


#%%

# reconstruct OD pairs 


# split into two dataframes
OD_pairs_df = pd.DataFrame(sample_df, columns =['Origins', 'Destinations'])
OD_pairs = OD_pairs_df.values.tolist()
OD_Origins = OD_pairs_df['Origins']
OD_Destinations = OD_pairs_df['Destinations']
OD_Origins_Arrary = OD_Origins.to_numpy()
OD_Destinations_Arrary = OD_Destinations.to_numpy()
#%%
# find all routes and all route distances 
routes = []
distances = []

#%%

print("Starting OD Processing...")
for a,b in OD_pairs:
    route = edges_pdna.shortest_paths(OD_Origins_Arrary,OD_Destinations_Arrary)
    #routes.append(route)
#%%

print("Finished OD Processing")
# create column of combined pairs
edges['route_pairs'] = edges['node_start'].astype(str) + ',' + edges['node_end'].astype(str)
#%%

# create dataframe of pairs at each end of a edge
route_pairs = []

# loop through all routes (as a list) to store all the pair values
for route in route:
    for i in range(len(route) -1 ):
        temp = str(route[i]) + "," + str(route[i+1])
        route_pairs.append(temp)
#%%
# converting list into dataframe for comparsion between route pairs and egdes
routes_df = pd.DataFrame({'route_pairs':route_pairs})


#%%
routes_df_reversed = routes_df.route_pairs.str.split(pat=',',expand=True)
routes_df_reversed = routes_df_reversed.rename(columns= {0:'node_start',1:'node_end'})
routes_df_reversed = routes_df_reversed['node_end'] + ',' + routes_df_reversed['node_start']
routes_df_reversed = routes_df_reversed.rename(str('route_pairs'), inplace=True)
routes_df_reversed = routes_df_reversed.to_frame()
#%%

# calculate the number of passes through each edge
passes_df = routes_df[routes_df['route_pairs'].isin(edges['route_pairs'])]
passes_df.groupby("route_pairs").size().sort_values(ascending=False)
passes_output_df = passes_df.groupby("route_pairs").size().reset_index(name="Passes")

#%%

# calculate the number of passes through each edge
passes_df_reversed = routes_df_reversed[routes_df_reversed['route_pairs'].isin(edges['route_pairs'])]
passes_df_reversed.groupby("route_pairs").size().sort_values(ascending=False)
passes_output_df_reversed = passes_df_reversed.groupby("route_pairs").size().reset_index(name="Passes_reversed")
#%%

# join the passes dataframe to the edges dataframe
edges = pd.merge(edges, passes_output_df, on ='route_pairs', how = 'left').fillna(0)
edges = pd.merge(edges, passes_output_df_reversed, on ='route_pairs', how = 'left').fillna(0)
edges['total_passes'] = edges['Passes'] + edges['Passes_reversed']
#%%

edges.to_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Bike Network\bike_network_routeuseage.shp')


end = time.time()

print("Execution time is:", end-start, "seconds")