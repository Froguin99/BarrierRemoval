# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 11:39:04 2022

@author: b8008458
"""
# Standard imports
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import geopandas as gpd
import matplotlib.pyplot as plt

#%%

# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\FullBarrierLayer.shp
bc = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\BikeNetwork\bike_network_costs_bc.shp')
ru = gpd.read_file(r'C:\Users\b8008458\Documents\2021_2022\Scratch Space\BikeNetwork\bike_network_routeuseage.shp')
barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersJoinGPKG.gpkg")
#%%

# join dfs
join = ru.merge(bc, on = 'geometry', how='left', suffixes=('', '_y'))
join.drop(join.filter(regex='_y$').columns, axis=1, inplace=True)

join = pd.DataFrame(join)

#%%

# plot

join.plot(x='Betweennes', y='total_pass', kind='scatter', c='cornflowerblue', xlabel='Edge Betweenness', ylabel='Edge passes', figsize=(7, 6))

#%%

join.plot(x='highway', y= 'total_pass')


#%%
 
# calculate Pearsons Coreelation Coofifient

correlation = join.corr()
print(correlation.loc['Betweennes', 'total_pass'])


#%%

barriers_df = pd.DataFrame(barriers)

#%%
barriers['minimum_ga'].plot(kind='bar', figsize=(7, 6), xlabel='Barrier ID', ylabel='Minimum Distance Gained (Meters)')