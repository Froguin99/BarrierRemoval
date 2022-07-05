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
barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\FullBarrierLayer.shp")


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\ODMatrix.shp
QGIS_OD_Matrix = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\NetworkTesting\ODMatrix.shp")


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

barriers['minimum_gain'] = min_network_distances_df['total_cost']


#%%

# export barriers

barriers.to_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\FullBarrierLayer.shp')