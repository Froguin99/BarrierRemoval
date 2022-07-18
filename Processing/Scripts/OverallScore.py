# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 21:31:30 2022

@author: b8008458
"""
# Standard imports
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import geopandas as gpd

#%%


# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\FullBarrierLayer.shp
barriersBC = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersBCJoin.shp")
barriersRU = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersRouteUseageJoin.shp")

#%%

barriersBC.drop(['cost','to', 'from_', 'length','v','u', 'oneway'], axis=1, inplace=True)
barriersRU.drop(['cost','to', 'from_', 'length','v','u', 'oneway'], axis=1, inplace=True)


#%%

join = barriersRU.merge(barriersBC, on = 'objectid', how='left', suffixes=('', '_y'))
join.drop(join.filter(regex='_y$').columns, axis=1, inplace=True)

join.set_crs(crs='EPSG:27700', allow_override=True)
#%%

join = gpd.GeoDataFrame(join)


join.to_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersJoin.shp")
