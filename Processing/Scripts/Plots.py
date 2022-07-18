# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 22:29:18 2022

@author: b8008458
"""
# Standard imports
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import geopandas as gpd

#%%

# data can be found under ...Github\BarrierRemoval\Data\Test Data\Python\FullBarrierLayer.shp
barriers = gpd.read_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersJoinGPKG.gpkg")

#%%

# normliase all mertics
barrier_copy = barriers[['barriersBCJoin_Betweennes','total_pass', 'minimum_ga','Critical_1']]

# inverse weighting for barriers as wider barriers are better barriers :)
barrier_copy['Critical_1'] *= -1

for column in barrier_copy:
    barrier_copy[column] = (barrier_copy[column] - barrier_copy[column].min()) / (barrier_copy[column].max() - barrier_copy[column].min())
#%%
    
import matplotlib.pyplot as plt
barrier_copy.plot(kind = 'bar', figsize=(10,6), xlabel='Barrier ID', ylabel='Normalised Score')
plt.legend(['Edge Betweenness', 'Edge Useage','Minimum Distance Gain','Critical Width'], loc='center left', bbox_to_anchor=(1.0, 0.9))
plt.show()

#%%

barrier_copy.plot(x='barriersBCJoin_Betweennes', y='total_pass', kind='scatter', c='cornflowerblue', xlabel='Edge Betweenness', ylabel='Edge passes')


#%%

# FINAL SCORING
cols = ['barriersBCJoin_Betweennes','total_pass', 'minimum_ga','Critical_1']

barrier_copy['Overall_Score'] = barrier_copy[cols].sum(axis=1)

barrier_copy['Overall_Score'].plot(kind = 'bar', figsize=(10,6), color='cornflowerblue', xlabel='Barrier ID', ylabel='Overall Score')


#%%

# join final scores back to original barrier dataset

# set indexs to join on
barrier_copy['Index'] = barrier_copy.index
barriers['Index'] = barriers.index

# join 
barrier_copy = gpd.GeoDataFrame(barrier_copy)
join = barriers.merge(barrier_copy, on = 'Index', how='left', suffixes=('', '_y'))
join.drop(join.filter(regex='_y$').columns, axis=1, inplace=True)


#%%

join.to_file(r"C:\Users\b8008458\Documents\2021_2022\Scratch Space\TestResults\barriersScored.shp")