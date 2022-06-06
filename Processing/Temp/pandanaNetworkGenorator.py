import geopandas as gpd
import pandana as pdna
import pandas as pd
import momepy 
import networkx as nx

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



# convert the data into the correct format for pandana

nodes, edges = momepy.nx_to_gdf(
    momepy.gdf_to_nx(
        network.explode()
    )
)

nodes = nodes.set_index("nodeID")

#%%

# create pandana network 
network_pdna = pdna.Network( 
    nodes.geometry.x,
    nodes.geometry.y,
    edges['node_start'], # set origins
    edges['node_end'], # set destinations
    edges[['mm_len']] # set weights
)

#%%

# snap barriers to network

network_pdna.set_pois(category='barriers', maxdist= 1000000, maxitems=1000, x_col = barriers.geometry.x, y_col = barriers.geometry.y )

# using ababritaty numbers

#%%


results = network_pdna.nearest_pois(distance = 1000000, category='barriers', num_pois = 10, include_poi_ids=True)

distances = results.iloc[:,:round(len(results.columns)/2,)] # create df with distances
pois_ids = results.iloc[:,round(len(results.columns)/2,):] # create df with pois ids

#%%

# convert wide matrices to long
distances_long = pd.melt(distances.reset_index(), id_vars='nodeID',value_name='distance') # make matrix long
pois_ids_long = pd.melt(pois_ids.reset_index(), id_vars='nodeID',value_name='poiID') # make matrix long

# create an od long df containing nodeID, distance, and poiID
od = distances_long
od['poiID'] = pois_ids_long['poiID'].astype('Int64') # set a column with pois ids (as they are indexed, they are already in the right order)

# format od matrix and drop NAs
od = od[['nodeID','poiID','distance']] # clean columns
od = od.dropna() # drop NAs

