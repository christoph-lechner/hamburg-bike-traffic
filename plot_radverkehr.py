#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib # for LogNorm()
import numpy as np
import pandas as pd
import geopandas as gpd
from db_conn import get_db_conn

def plot_city(hax):
    """
    Helper function to plot geographical information such as city limits
    """
    gdf = gpd.read_file('mapdata/Hamburg_Stadtteilestatistik.shp')
    print(gdf.crs) # info from .prj file

    # Note: could add map using contextily, here we do need Web Mercator (EPSG:3857)
    # list of EPSG codes https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset
    gdf = gdf.to_crs(epsg=4326) # latitude/longitude
    gdf.plot(ax=hax, color='white', edgecolor='blue')


def plot_traffic_dailytotal(cur, *, date='2026-02-12', hax=None):
    cur.execute(
        """
        SELECT iot_id,longitude,latitude,DATE(t_start) AS date, COUNT(*) AS c, SUM(result) AS s
        FROM bikeproj_zaehlstellen
        WHERE DATE(t_start)=%s AND richtung<>'Querschnitt'
        GROUP BY iot_id,longitude,latitude,DATE(t_start)
        ORDER BY s DESC,iot_id ASC;
        """,
        (date,)
    )

    res_rows = cur.fetchall()
    if len(res_rows)==0:
        print(f'Info: No data in DB for date={date}. Not drawing plot.')
        return

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

    do_standalone=False
    if hax is None:
        fig,hax = plt.subplots(1, figsize=(12,8))
        plot_city(hax)
        do_standalone=True

    hsc = hax.scatter(
            filtered_df['longitude'], filtered_df['latitude'],
            s=marker_sizes,
            c=filtered_df['daily_total'], alpha=0.5,
            cmap='viridis', norm=matplotlib.colors.LogNorm(vmin=10,vmax=10000)
    )
    cbar = plt.colorbar(hsc)
    cbar.set_label(f'total number of bikes on {date}')

    # indicate positions of counters
    hax.plot(filtered_df['longitude'], filtered_df['latitude'], 'k+')

    if do_standalone:
        hax.set_xlabel('longitude')
        hax.set_ylabel('latitude')
        plt.show()



def plot_traffic_ratio_2days(cur, *, date1 = '2026-02-11', date2 = '2026-02-16', hax=None):
    # For meaning of date1 and date2, see definition of 'r' in SQL query
    # -> date1 is denominator

    cur.execute(
        """
        WITH qq AS (
            WITH q AS (
                SELECT iot_id,DATE(t_start) AS date,latitude,longitude,SUM(result) AS s FROM bikeproj_zaehlstellen
                WHERE DATE(t_start)=%s OR DATE(t_start)=%s AND richtung<>'Querschnitt'
                GROUP BY iot_id,date,latitude,longitude
                ORDER BY iot_id,date
            )
            SELECT
                iot_id,latitude,longitude,
                SUM((CASE WHEN date=%s THEN s END)) AS s1,
                SUM((CASE WHEN date=%s THEN s END)) AS s2
            FROM q
            GROUP BY iot_id,latitude,longitude
        )
        SELECT
            iot_id,latitude,longitude, s1, s2,  s2/s1 AS r
        FROM qq
        WHERE s1>0 AND s1 IS NOT NULL AND s2 IS NOT NULL;
        """,
        (date1,date2,date1,date2)
    )

    res_rows = cur.fetchall()
    if len(res_rows)==0:
        print(f'Info: No data in DB for dates {date1} and {date2}. Not drawing plot.')
        return

    accu_data=[]
    for row in res_rows:
        accu_data.append({'longitude':row['longitude'], 'latitude':row['latitude'], 'ratio':row['r']})

    df = pd.DataFrame(accu_data)
    filtered_df = df[(df['longitude']!=0) & (df['latitude']!=0)]
    n_kickedout = len(df)-len(filtered_df)
    if n_kickedout:
        print(f'Info: Removed {n_kickedout} datapoints before plotting because coordinates are zero')

    marker_sizes = 100 # !marker area

    do_standalone=False
    if hax is None:
        fig,hax = plt.subplots(1, figsize=(12,8))
        plot_city(hax)
        do_standalone=True

    hsc = hax.scatter(
            filtered_df['longitude'], filtered_df['latitude'],
            s=marker_sizes,
            c=filtered_df['ratio'], alpha=0.5,
            cmap='viridis',
            # norm=matplotlib.colors.LogNorm(vmin=0.1,vmax=1)
            vmin=0.1,vmax=1
    )
    cbar = plt.colorbar(hsc)
    cbar.set_label(f'traffic ratio {date2}/{date1}')

    # indicate positions of counters
    hax.plot(filtered_df['longitude'], filtered_df['latitude'], 'k+')

    if do_standalone:
        hax.set_xlabel('longitude')
        hax.set_ylabel('latitude')
        plt.show()


def timeplot(cur,hax,date='2026-02-11'):
    cur.execute(
        """
        SELECT t_start, COUNT(*) AS count, SUM(result) AS s
        FROM bikeproj_zaehlstellen
        WHERE DATE(t_start)=%s AND richtung<>'Querschnitt'
        GROUP BY t_start
        ORDER BY t_start ASC;
        """,
        (date,)
    )

    res_rows = cur.fetchall()
    accu_data=[]
    for row in res_rows:
        accu_data.append({'timestamp':row['t_start'], 'ndatarows':row['count'], 'total':row['s']})

    if len(accu_data)==0:
        print(f'Warning: there appears to be no data for date={date}')
        return

    df = pd.DataFrame(accu_data)
    hax.plot(df['timestamp'], df['total'], label=f'{date}')

def main():
    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)

    plot_traffic_dailytotal(cur, date='2026-03-04')
    plot_traffic_dailytotal(cur, date='2026-03-01')
    plot_traffic_ratio_2days(cur)

    ### TEST: write .png file ###
    # With caller-provided axes handle, we have more control over the plot's appearance (but this means extra work)
    fig,hax = plt.subplots(figsize=(12,8))
    plot_city(hax)
    plot_traffic_dailytotal(cur, date='2026-03-04', hax=hax)
    hax.set_xlabel('longitude')
    hax.set_ylabel('latitude')
    plt.savefig('x.png', dpi=150, bbox_inches='tight')
    plt.show()


    """
    fig,hax = plt.subplots(1, figsize=(12,8))
    timeplot(cur,hax,'2026-02-11')
    timeplot(cur,hax,'2026-02-12')
    timeplot(cur,hax,'2026-02-13')
    timeplot(cur,hax,'2026-02-14')
    timeplot(cur,hax,'2026-02-15')
    timeplot(cur,hax,'2026-02-16')
    timeplot(cur,hax,'2026-02-17')
    timeplot(cur,hax,'2026-02-18')
    hax.legend()
    plt.show()
    """


if __name__=='__main__':
    main()
