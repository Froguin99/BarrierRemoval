# -*- coding: utf-8 -*-
"""
Created on Mon Jul  4 11:42:01 2022

@author: b8008458
"""

# Standard imports
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import geopandas as gpd


#%%

# Import barriers 


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\FullBarrierLayer.shp
barriers = gpd.read_file(r"C:\Users\b8008458\OneDrive - Newcastle University\2021 to 2022\Dissertation\Github\BarrierRemoval\Study Areas\Pembrokeshire\Barriers\PembrokeBarriers.gpkg")



# Import OD Matrix from QGIS


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\ODMatrix.shp
QGIS_OD_Matrix = gpd.read_file(r"C:\Users\b8008458\OneDrive - Newcastle University\2021 to 2022\Dissertation\Github\BarrierRemoval\Study Areas\Pembrokeshire\ODMatrix\PembrokeODMatrix.shp")




#%%

# remove i - i and j - j 
QGIS_OD_Matrix = QGIS_OD_Matrix[QGIS_OD_Matrix['origin_id'] != QGIS_OD_Matrix['destinatio']]

#%%

# calculate minium network distance 
min_network_distances_df = QGIS_OD_Matrix.groupby('origin_id')['total_cost'].min()

#%%
# convert to dataframe
min_network_distances_df = min_network_distances_df.to_frame().reset_index() 

#%%

# join minimum distances to barriers
barriers['origin_id'] = barriers['globalid']

join = barriers.merge(min_network_distances_df, on = 'origin_id', how='left', suffixes=('', '_y'))
join.drop(join.filter(regex='_y$').columns, axis=1, inplace=True)




#%%

# export barriers

join.to_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Barriers\YorkBarriers.shp")