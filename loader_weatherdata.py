#!/usr/bin/env python3

import psycopg
import requests
import datetime


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

def get_data(cur, stg_table):
    # Coordinates for Hamburg, Germany
    lat, lon = 53.55, 10.00

    # str_date = '2026-02-12' # date to be specified in UTC
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
        if curr_source['observation_type']=='current':
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
        # we want only actual measurements -> reject any forecasts, etc.
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
    # Password in ~/.pgpass, line format
    # hostname:port:database:username:password
    # !mode has to be 600!
    conn = psycopg.connect(dbname = 'dev', 
                           user = 'dev', 
                           host= '192.168.2.253',
                           port = 15432)
    cur = conn.cursor()

    # prepare staging table
    t0 = datetime.datetime.now()
    str_t0 = t0.strftime('%Y%m%dT%H%M%S')
    stg_table = 'stg_weather' # 'stg_weather_'+str_t0

    prepare_stg_table(cur, stg_table)
    nloaded = get_data(cur, stg_table)
    nmerged = data_merge(cur, stg_table)

    conn.commit()
    cur.close()
    conn.close()

    print(f'{nloaded} {nmerged}')

if __name__=='__main__':
    main()
