#!/usr/bin/env python3

import psycopg
import requests
import datetime
from db_conn import get_db_conn


def prepare_stg_table(cur, stg_table):
    cur.execute(
        f"""
        CREATE TEMPORARY TABLE {stg_table} (
            ts_entry_creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            query_lat FLOAT,
            query_lon FLOAT,

            timestamp TIMESTAMP WITH TIME ZONE,
            source_id INT,
            precipitation FLOAT,
            pressure_msl FLOAT,
            sunshine INT,
            temperature FLOAT,
            wind_direction INT,
            wind_speed FLOAT,
            cloud_cover FLOAT,
            dew_point FLOAT,
            relative_humidity INT,
            visibility INT,
            wind_gust_direction INT,
            wind_gust_speed FLOAT,
            precipitation_probability INT,
            precipitation_probability_6h INT,
            solar FLOAT,
            condition TEXT,
            icon TEXT,
            UNIQUE (timestamp,query_lat,query_lon)
        );
        """
    )

def get_data(cur, stg_table, str_date=None):
    # Coordinates for Hamburg, Germany
    lat, lon = 53.55, 10.00

    if str_date is None:
        str_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')

    # print(str_date)
    params = {
        'date': str_date,
        'lat': lat,
        'lon': lon,
    }
    url = 'https://api.brightsky.dev/weather'
    response = requests.get(url, params=params)
    data = response.json()

    # determine source describing actual measurements
    meas_source_ids=[]
    for curr_source in data['sources']:
        if curr_source['observation_type'] in ['current','historical']:
            meas_source_ids.append(curr_source['id'])

    # field names in DB
    db_fields = [
        'timestamp', 'source_id', 'precipitation', 'pressure_msl', 'sunshine', 'temperature', 'wind_direction', 'wind_speed', 'cloud_cover', 'dew_point', 'relative_humidity', 'visibility', 'wind_gust_direction', 'wind_gust_speed', 'precipitation_probability', 'precipitation_probability_6h', 'solar',
        #
        # According to brightsky.de documentation, these fields are "not taken as-is from the raw data (because it does not exist)". They are calculated from different fields in the raw data as a best effort.
        'condition', 'icon'
    ]
    # field names in brightsky.dev JSON response
    src_fields = [
        'timestamp', 'source_id', 'precipitation', 'pressure_msl', 'sunshine', 'temperature', 'wind_direction', 'wind_speed', 'cloud_cover', 'dew_point', 'relative_humidity', 'visibility', 'wind_gust_direction', 'wind_gust_speed', 'precipitation_probability', 'precipitation_probability_6h', 'solar',
        #
        # According to brightsky.de documentation, these fields are "not taken as-is from the raw data (because it does not exist)". They are calculated from different fields in the raw data as a best effort.
        'condition', 'icon'
    ]


    all_db_fields = ['query_lat','query_lon'] # ts_entry_creation will be set automatically
    all_db_fields.extend(db_fields)
    N_all_db_fields = len(all_db_fields)
    q_all_db_fields = ','.join(all_db_fields)
    q_all_db_fields_placeholders = ','.join(['%s']*N_all_db_fields)

    ndata=0
    for curr_m in data['weather']:
        # we want only actual measurements (historical data is accepted as well, it has different id) -> reject any forecasts, etc.
        if not (curr_m['source_id'] in meas_source_ids):
            continue

        values=[lat,lon]
        for k in src_fields:
            values.append(curr_m[k])
        # print(values)
        cur.execute(
            'INSERT INTO '+stg_table+f' ({q_all_db_fields}) VALUES ({q_all_db_fields_placeholders})',
            tuple(values)
        )
        ndata+=1
    return ndata

def data_merge(cur, stg_table):
    data_table = 'bikeproj_weather'
    cur.execute(
        f"""
        MERGE
        INTO
            {data_table} AS dst
        USING
            {stg_table} AS src
        ON
            dst.timestamp=src.timestamp AND dst.query_lat=src.query_lat AND dst.query_lon=src.query_lon
        WHEN MATCHED THEN
            UPDATE SET
                timestamp=src.timestamp,
                source_id=src.source_id,
                precipitation=src.precipitation,
                pressure_msl=src.pressure_msl,
                sunshine=src.sunshine,
                temperature=src.temperature,
                wind_direction=src.wind_direction,
                wind_speed=src.wind_speed,
                cloud_cover=src.cloud_cover,
                dew_point=src.dew_point,
                relative_humidity=src.relative_humidity,
                visibility=src.visibility,
                wind_gust_direction=src.wind_gust_direction,
                wind_gust_speed=src.wind_gust_speed,
                precipitation_probability=src.precipitation_probability,
                precipitation_probability_6h=src.precipitation_probability_6h,
                solar=src.solar,
                condition=src.condition,
                icon=src.icon
        WHEN NOT MATCHED THEN
            INSERT VALUES (ts_entry_creation,query_lat,query_lon,timestamp,source_id,precipitation,pressure_msl,sunshine,temperature,wind_direction,wind_speed,cloud_cover,dew_point,relative_humidity,visibility,wind_gust_direction,wind_gust_speed,precipitation_probability,precipitation_probability_6h,solar,condition,icon);
        """
    )

    # row count includes INSERTs and UPDATEs
    return cur.rowcount


def main():
    conn = get_db_conn()
    cur = conn.cursor()
    print('DB connection established')

    # Prepare TWO staging tables
    # Reason: There is 1 hour of temporal overlap of the returned data (the query for historical data results in 25 hours of data)
    tstart = datetime.datetime.now()
    str_tstart = tstart.strftime('%Y%m%dT%H%M%S')
    stg_table  = 'stg_weather' # 'stg_weather_'+str_tstart
    stg_table2 = stg_table+'_2'
    prepare_stg_table(cur, stg_table)
    prepare_stg_table(cur, stg_table2)

    t0 = datetime.datetime.now(datetime.timezone.utc)
    str_date = t0.strftime('%Y-%m-%d')
    print(f'Obtaining weather data for {str_date} (in timezone UTC) ...')
    nloaded = get_data(cur, stg_table, str_date=str_date)
    nmerged = data_merge(cur, stg_table)
    print(f'loaded:{nloaded} merged:{nmerged}')

    # also obtain historical data from day before today (to avoid any gaps when data is obtained only a few times per day -- the response only contains one complete day)
    str_date = (t0+datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
    print(f'Obtaining weather data for {str_date} (in timezone UTC) ...')
    nloaded = get_data(cur, stg_table2, str_date=str_date)
    nmerged = data_merge(cur, stg_table2)
    print(f'loaded:{nloaded} merged:{nmerged}')


    conn.commit()
    cur.close()
    conn.close()


if __name__=='__main__':
    main()
