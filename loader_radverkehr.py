#!/usr/bin/env python3

# Christoph Lechner, 2026-Feb

import psycopg
import requests
import datetime
import time
import traceback
import numpy as np
import json
import signal
import gzip
from dataclasses import dataclass, asdict
from functools import partial
from pathlib import Path
from my_util import deep_get
from db_conn import get_db_conn


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

# URL to get two weeks of data ('top' parameter was changed)
API_URL = 'https://iot.hamburg.de/v1.1/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_HamburgerRadzaehlnetz%27%20and%20Datastreams/properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27&$expand=Datastreams($filter=properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27;$expand=Observations($top=1344;$orderby=phenomenonTime%20desc))&$count=true&$top=1000&$orderBy=@iot.id'

### HTTP request timeouts ###
timeout_transfer = 300 # seconds, timeout for whole transfer

# Note that the following do not limit the duration of the whole transfer
timeout_connect = 30 # seconds
timeout_read = 30 # seconds (time client will wait between receiving bytes from the server, see documentation https://requests.readthedocs.io/en/latest/user/advanced/#timeouts )

datadir = Path('data/')

class TimeoutException(Exception):
    pass

def handler(signum, frame):
    raise TimeoutException('Total timeout for download exceeded')




def prepare_stg_table(cur, stg_table):
    # schema identical to "bikeproj_zaehlstellen" schema in schema.sql
    cur.execute(
        f"""
        CREATE TEMPORARY TABLE {stg_table} (
            iot_id INT,
            name TEXT,
            longitude FLOAT,
            latitude FLOAT,
            ds_name TEXT,
            richtung TEXT,
            str_phenomenonTime TEXT,
            t_start TIMESTAMP WITH TIME ZONE,
            t_end TIMESTAMP WITH TIME ZONE,
            result INT,
            remark TEXT,
            UNIQUE (iot_id,name,str_phenomenonTime)
        );
        """
    )

@dataclass
class Observation:
    iot_id: int
    name: str
    longitude: float
    latitude: float
    ds_name: str
    richtung: str
    #
    phenomenonTime: str
    pt_split0: str
    pt_split1: str
    result: int # FIXME: the name "result" should be changed, it reflects the name of this property in JSON response
    #
    remark: str

def process_data(data, *, cb=None):
    """
    'data' contains the decoded JSON response from a single API request
    'cb' is the callback function that will be called with Observations. If 'cb' is not provided, this function parses the data but otherwise has no effect
    """
    def helper_PT(s):
        """
        Helper function to break up the time format returned by Hamburg IOT Server
        Example value in 'phenomenonTime': "2026-02-11T16:15:00Z/2026-02-11T16:29:59Z"
        """
        s_split = s.split('/')
        if len(s_split)>2:
            raise ValueError('expecting format "datetime1/datetime2"')
        return s_split

    # Loop over all stations in the dataset
    ndata=0
    for zaehlstelle in data['value']:
        # Here we collect any free-text remarks (or 'None'/NULL if there are none)
        remark = None

        iot_id = deep_get(zaehlstelle, '@iot.id')

        # Most stations have coordiate type 'Point'
        curr_coords=None # value will be overwritten in the following
        if deep_get(zaehlstelle,['Datastreams',0,'observedArea','type'])=='Point':
            curr_coords=deep_get(zaehlstelle,['Datastreams',0,'observedArea','coordinates'])
        elif deep_get(zaehlstelle,['Datastreams',0,'observedArea','type'])=='LineString':
            # Some stations have coordinate of type 'LineString', for instance "[9.999377, 53.580126],[9.999282, 53.580056]" (for @iot.id=5564)
            # Current approach (TODO: think about better solutions):
            # 1) preserve coordinate information in 'remark' field
            # 2) take average of the coordinates and store as longitude/latitude
            #
            # FIXME: check if the two points are in close proximity? -> Haversine formel
            complete_coords=deep_get(zaehlstelle,['Datastreams',0,'observedArea','coordinates'])
            if len(complete_coords)>2:
                # As of Feb-2026, the LineString value only comprises 2 points, but it could have more (currently not supported)
                print(f'skipping Zaehlstelle @iot.id={iot_id}: unknown coordinate type (program only supports LineString with 2 points)')
                continue
            remark = 'coordinates: '+json.dumps(complete_coords)
            curr_coords = np.mean(complete_coords, axis=0).tolist()
            # print(curr_coords)
        else:
            print(f'skipping Zaehlstelle @iot.id={iot_id}: unknown coordinate type')
            continue

        # format most recent observation (i.e. bike traffic in last 15 minutes) into string
        if (observations:=deep_get(zaehlstelle,['Datastreams',0,'Observations'])) is None:
            print('skipping Zaehlstelle: there are no observations to process')
            continue

        name = deep_get(zaehlstelle, 'name')
        longitude = curr_coords[0]
        latitude  = curr_coords[1]
        ds_name = deep_get(zaehlstelle,['Datastreams',0,'name'])
        richtung = deep_get(zaehlstelle,['properties','richtung'])

        # Remark: some Zaehlstellen don't have observations, for instance @iot.id==9470
        for curr_obs in observations:
            pt_split = helper_PT(curr_obs['phenomenonTime'])
            obs = Observation(
                iot_id=iot_id, 
                name=name,
                longitude=longitude,
                latitude=latitude,
                ds_name=ds_name,
                richtung=richtung,
                phenomenonTime=curr_obs['phenomenonTime'],
                pt_split0=pt_split[0],
                pt_split1=pt_split[1],
                result=curr_obs['result'],
                remark=remark
            )
            if cb:
                cb(obs)
            ndata+=1
    return ndata

def get_data(cur, stg_table, url=API_URL, my_cb=None):
    tstartreq = datetime.datetime.now()
    partcntr=1
    datasets = []
    while url:
        # Before performing the API request, install timeout. Here execution time is beyond our control (for instance, if server reacts very slowly).
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_transfer)

        try:
            print('*** requesting data ***')
            response = requests.get(url, timeout=(timeout_connect,timeout_read))
            response.raise_for_status() # exception when HTTP status code is 4xx or 5xx
            print('*** request complete ***')

            fn_dump = datadir / ('dump_' + tstartreq.strftime('%Y%m%dT%H%M%S') + '_' + f'{partcntr:06d}' + '.gz')
            with gzip.open(fn_dump,'wb') as fout:
                fout.write(response.content)
        except TimeoutException:
            print('reached total timeout')
            raise

        signal.alarm(0) # disable timeout after critical section

        # decode JSON in response body and store it for the processing step that follows
        data = response.json()
        datasets.append(data)

        # If there is more data, prepare follow-up request
        url = None
        if '@iot.nextLink' in data:
            url = data['@iot.nextLink']
            partcntr+=1

    ndatatot=0
    for data in datasets:
        ndatatot += process_data(data, cb=my_cb)

    print('*** done processing returned data ***')
    return ndatatot


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
            UPDATE SET longitude=src.longitude, latitude=src.latitude, ds_name=src.ds_name, richtung=src.richtung, t_start=src.t_start, t_end=src.t_end, result=src.result, remark=src.remark
        WHEN NOT MATCHED THEN
            INSERT VALUES (iot_id,name,longitude,latitude,ds_name,richtung,str_phenomenonTime,t_start,t_end,result,remark);
        """
    )
    return cur.rowcount



##########################
### CALLBACK FUNCTIONS ###
##########################

def process_data_cb_sqlinsert(obs, *, cur, stg_table):
    cur.execute(
        'INSERT INTO '+stg_table+' (iot_id,name,longitude,latitude,ds_name,richtung,str_phenomenonTime,t_start,t_end,result,remark) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (obs.iot_id,obs.name,obs.longitude,obs.latitude,obs.ds_name,obs.richtung,   obs.phenomenonTime,obs.pt_split0,obs.pt_split1, obs.result, obs.remark)
    )

def process_data_cb_collect(obs, *, l):
    l.append(obs)

##########################

def main():
    conn = get_db_conn()
    cur = conn.cursor()

    # prepare staging table
    t0 = datetime.datetime.now()
    str_t0 = t0.strftime('%Y%m%dT%H%M%S')
    stg_table = 'stg' # 'stg_'+str_t0
    prepare_stg_table(cur, stg_table)

    # my_cb = partial(process_data_cb_sqlinsert, cur=cur, stg_table=stg_table)
    l_obs=[]
    my_cb = partial(process_data_cb_collect, l=l_obs)
    ndata_from_source = get_data(cur, stg_table, my_cb=my_cb)
    print(l_obs[0])

    ndata_merged = data_merge(cur, stg_table)

    conn.commit()
    cur.close()
    conn.close()

    print(f'row statistics: {ndata_from_source} {ndata_merged}')

if __name__=='__main__':
    main()
