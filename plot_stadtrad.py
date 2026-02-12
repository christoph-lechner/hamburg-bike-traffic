#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

fn_in = 'out_series_stadtrad/log_20260210T191227.txt'
        # 'out_series_stadtrad/log_20260210T002046.txt'

gdf = gpd.read_file('mapdata/Hamburg_Stadtteilestatistik.shp')
print(gdf.crs) # info from .prj file

# Note: could add map using contextily, here we do need Web Mercator (EPSG:3857)
# list of EPSG codes https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset
gdf = gdf.to_crs(epsg=4326) # latitude/longitude

df = pd.read_csv(fn_in, names=['id', 'timestamp', 'nbikes', 'longitude', 'latitude', 'name'])
filtered_df = df[(df['longitude']!=0) & (df['latitude']!=0)]
n_kickedout = len(df)-len(filtered_df)
if n_kickedout:
    print(f'Info: Removed {n_kickedout} datapoints before plotting because coordinates are zero')

fig,hax = plt.subplots(1, figsize=(12,8))
gdf.plot(ax=hax, color='white', edgecolor='blue')
hax.plot(filtered_df['longitude'], filtered_df['latitude'], 'k+')

plt.show()
