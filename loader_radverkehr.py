#!/usr/bin/env python3

# Christoph Lechner, 2026-Feb

import psycopg
import requests
import datetime
import time
import traceback
from my_util import deep_get

# Infos about parameters in the request:
# https://fraunhoferiosb.github.io/FROST-Server/sensorthingsapi/requestingData/STA-Tailoring-Responses.html
#
# original URL:
# API_URL = 'https://iot.hamburg.de/v1.1/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_HamburgerRadzaehlnetz%27%20and%20Datastreams/properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27&$count=true&$expand=Datastreams($filter=properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27;$expand=Observations($top=10;$orderby=phenomenonTime%20desc))'
#
# The original URL was modified as follows:
# 1) It does not define the sort order of the objects.
# 2) Currently there are 311 objects in total. Ask the server to deliver a maximum of 1000 objects by specifying the 'top' parameter. Then all data is obtained in a single request.
API_URL = 'https://iot.hamburg.de/v1.1/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_HamburgerRadzaehlnetz%27%20and%20Datastreams/properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27&$expand=Datastreams($filter=properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27;$expand=Observations($top=10;$orderby=phenomenonTime%20desc))&$count=true&$top=1000&$orderBy=@iot.id'



def prepare_stg_table(cur, stg_table):
    cur.execute(
        f"""
        CREATE TEMPORARY TABLE {stg_table} (
            iot_id INT,
            name TEXT,
            longitude FLOAT,
            latitude FLOAT,
            ds_name TEXT,
            str_phenomenonTime TEXT,
            t_start TIMESTAMP WITH TIME ZONE,
            t_end TIMESTAMP WITH TIME ZONE,
            result INT,
            UNIQUE (iot_id,name,str_phenomenonTime)
        );
        """
    )


def get_data(cur, stg_table, url=API_URL):
    def helper_PT(s):
        """
        Example value in 'phenomenonTime': "2026-02-11T16:15:00Z/2026-02-11T16:29:59Z"
        """
        s_split = s.split('/')
        if len(s_split)>2:
            raise ValueError('expecting format "datetime1/datetime2"')
        return s_split

    while url:
        print('*** requesting data ***')
        response = requests.get(url)
        print(response)
        data = response.json()

        # If there is more data, prepare follow-up request
        url = None
        if '@iot.nextLink' in data:
            url = data['@iot.nextLink']

        # Loop over all stations in the dataset
        ndata=0
        for zaehlstelle in data['value']:
            # Workaround for first version: skip Zaehlstations that do not have coordinate type Point. This avoid coordinates such as "[9.999377, 53.580126],[9.999282, 53.580056]" (for @iot.id=5564) and help to develop the first version.
            if deep_get(zaehlstelle,['Datastreams',0,'observedArea','type'])!='Point':
                print('skipping Zaehlstelle: coordinate is not of type Point')
                continue

            curr_coords=deep_get(zaehlstelle,['Datastreams',0,'observedArea','coordinates'])
            # format most recent observation (i.e. bike traffic in last 15 minutes) into string
            if (observations:=deep_get(zaehlstelle,['Datastreams',0,'Observations'])) is None:
                print('skipping Zaehlstelle: there are no observations to process')
                continue

            iot_id = deep_get(zaehlstelle, '@iot.id')
            name = deep_get(zaehlstelle, 'name')
            longitude = curr_coords[0]
            latitude  = curr_coords[1]
            ds_name = deep_get(zaehlstelle,['Datastreams',0,'name'])

            # Remark: some Zaehlstellen don't have observations, for instance @iot.id==9470
            for curr_obs in observations:
                pt_split = helper_PT(curr_obs['phenomenonTime'])
                cur.execute(
                    'INSERT INTO '+stg_table+' (iot_id,name,longitude,latitude,ds_name,str_phenomenonTime,t_start,t_end,result) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (iot_id,name,longitude,latitude,ds_name,   curr_obs['phenomenonTime'],pt_split[0],pt_split[1], curr_obs['result'])
                )
                ndata+=1

    print('*** done processing returned data ***')
    return ndata


def data_merge(cur, stg_table):
    data_table = 'bikeproj_zaehlstellen'
    cur.execute(
        f"""
        MERGE
        INTO
            {data_table} AS dst
        USING
            {stg_table} AS src
        ON
            dst.iot_id=src.iot_id AND dst.name=src.name AND dst.str_phenomenonTime=src.str_phenomenonTime
        WHEN MATCHED THEN
            UPDATE SET longitude=src.longitude, latitude=src.latitude, ds_name=src.ds_name, t_start=src.t_start, t_end=src.t_end, result=src.result
        WHEN NOT MATCHED THEN
            INSERT VALUES (iot_id,name,longitude,latitude,ds_name,str_phenomenonTime,t_start,t_end,result);
        """
    )
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
    stg_table = 'stg' # 'stg_'+str_t0

    prepare_stg_table(cur, stg_table)
    ndata_from_source = get_data(cur, stg_table)
    ndata_merged = data_merge(cur, stg_table)

    conn.commit()
    cur.close()
    conn.close()

    print(f'row statistics: {ndata_from_source} {ndata_merged}')

if __name__=='__main__':
    main()
