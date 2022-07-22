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
barriersBC = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Spatail Joins\BCJoin.shp")
barriersRU = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Spatail Joins\RouteUseage.shp")
barriersIMD = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Spatail Joins\IDMandCarsJoin.shp")

#%%

barriersBC.drop(['cost','to', 'from_', 'length','v','u', 'oneway'], axis=1, inplace=True)
barriersRU.drop(['cost','to', 'from_', 'length','v','u', 'oneway'], axis=1, inplace=True)
#barriersIMD.drop(['cost','to', 'from_', 'length','v','u', 'oneway'], axis=1, inplace=True)


#%%

join1 = barriersRU.merge(barriersBC, on = 'globalid', how='left', suffixes=('', '_y'))
join1.drop(join1.filter(regex='_y$').columns, axis=1, inplace=True)

join2 = join1.merge(barriersIMD, on = 'globalid', how='left', suffixes=('', '_y'))
join2.drop(join2.filter(regex='_y$').columns, axis=1, inplace=True)

join2.set_crs(crs='EPSG:27700', allow_override=True)
#%%

join2 = gpd.GeoDataFrame(join2)


join2.to_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\York\Spatail Joins\barriersJoin.shp")
