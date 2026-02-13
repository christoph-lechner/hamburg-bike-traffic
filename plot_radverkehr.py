#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib # for LogNorm()
import numpy as np
import pandas as pd
import geopandas as gpd
from db_conn import get_db_conn

def plotgeo(hax):
    """
    Helper function to plot geographical information such as city limits
    """
    gdf = gpd.read_file('mapdata/Hamburg_Stadtteilestatistik.shp')
    print(gdf.crs) # info from .prj file

    # Note: could add map using contextily, here we do need Web Mercator (EPSG:3857)
    # list of EPSG codes https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset
    gdf = gdf.to_crs(epsg=4326) # latitude/longitude
    gdf.plot(ax=hax, color='white', edgecolor='blue')


def doit(cur):
    date = '2026-02-11'

    cur.execute(
        """
        SELECT iot_id,longitude,latitude,DATE(t_start) AS date, COUNT(*) AS c, SUM(result) AS s
        FROM bikeproj_zaehlstellen
        WHERE DATE(t_start)=%s
        GROUP BY iot_id,longitude,latitude,DATE(t_start)
        ORDER BY s DESC,iot_id ASC;
        """,
        (date,)
    )

    res_rows = cur.fetchall()
    accu_data=[]
    for row in res_rows:
        # expected format: {'iot_id': 7082, 'longitude': 9.935064, 'latitude': 53.555708, 'date': datetime.date(2026, 2, 11), 'c': 96, 's': 3545}
        accu_data.append({'longitude':row['longitude'], 'latitude':row['latitude'], 'ndatarows':row['c'], 'daily_total':row['s']})

    df = pd.DataFrame(accu_data)
    filtered_df = df[(df['longitude']!=0) & (df['latitude']!=0)]
    n_kickedout = len(df)-len(filtered_df)
    if n_kickedout:
        print(f'Info: Removed {n_kickedout} datapoints before plotting because coordinates are zero')

    max_marker_size = 1000 # !marker area
    max_daily_total = filtered_df['daily_total'].max()
    marker_sizes = max_marker_size * filtered_df['daily_total']/max_daily_total

    fig,hax = plt.subplots(1, figsize=(12,8))
    plotgeo(hax)
    hsc = hax.scatter(
            filtered_df['longitude'], filtered_df['latitude'],
            s=marker_sizes,
            c=filtered_df['daily_total'], alpha=0.5,
            cmap='viridis', norm=matplotlib.colors.LogNorm(vmin=10,vmax=10000))
    cbar = plt.colorbar(hsc)
    cbar.set_label(f'total number of bikes on {date}')

    # indicate positions of counters
    hax.plot(filtered_df['longitude'], filtered_df['latitude'], 'k+')

    hax.set_xlabel('longitude')
    hax.set_ylabel('latitude')

    plt.show()

def main():
    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)

    doit(cur)


if __name__=='__main__':
    main()
