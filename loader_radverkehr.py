#!/usr/bin/env python3

# Christoph Lechner, 2026-Feb

import psycopg
import datetime
import time
import traceback
import numpy as np
import gzip
from dataclasses import dataclass, asdict
from functools import partial
from pathlib import Path
import argparse
from my_util import deep_get
from getdata import get_data,get_api_URL
from procdata import process_data
from db_conn import get_db_conn


datadir = Path('data/')

# For HTTP request timeouts, see Python source file with download functions




# schema identical to "bikeproj_zaehlstellen" schema in schema.sql
datacol_ddl =
"""
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
            remark TEXT
"""


def prepare_stg_table(cur, stg_table):
    cur.execute(
        f"""
        CREATE TEMPORARY TABLE {stg_table} (
            {datacol_ddl},
            -- UNIQUE (iot_id,name,str_phenomenonTime)
        );
        """
    )


def store_data_stats(cur, stg_table, filename, is_scheduled, ndays_req):
    cur.execute(
        f"""
        SELECT
            COUNT(*) AS nrows,
            COUNT(DISTINCT iot_id) AS c_iot_ids,
            MIN(t_start) AS min_tstart,
            MAX(t_start) AS max_tstart,
            MIN(t_end) AS min_tend,
            MAX(t_end) AS max_tend
        FROM {stg_table}"""
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError('expected exactly one row with results, got none')

    print(row)
    stats_table='bikeproj_zaehlstellen_loaderstats'
    cur.execute(
        'INSERT INTO '+stats_table+' (filename,is_scheduled_run,ndays_req,  dataset_n_iot_ids, dataset_n_rows, dataset_min_tstart, dataset_max_tstart, dataset_min_tend, dataset_max_tend) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (filename,is_scheduled,ndays_req,  row['c_iot_ids'], row['nrows'], row['min_tstart'], row['max_tstart'], row['min_tend'], row['max_tend'])
    )



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

#####################
### MAIN FUNCTION ###
#####################

def main(*, ndays=10, is_scheduled=None):
    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)


    # prepare staging table
    t0 = datetime.datetime.now()
    str_t0 = t0.strftime('%Y%m%dT%H%M%S')
    stg_table = 'stg' # 'stg_'+str_t0
    prepare_stg_table(cur, stg_table)

    ###
    # CB function inserting data into the DB
    my_row_cb = partial(process_data_cb_sqlinsert, cur=cur, stg_table=stg_table)
    # CB function to collect data in a list (nothing is inserted into the DB!)
    l_obs=[]
    # my_row_cb = partial(process_data_cb_collect, l=l_obs)
    ###

    def cb_store_gzip(*, response, tstartreq=None, partcntr=1):
        fn_without_path = 'dump_' + tstartreq.strftime('%Y%m%dT%H%M%S') + '_' + f'{partcntr:06d}' + '.gz'
        fn_dump = datadir / fn_without_path
        with gzip.open(fn_dump,'wb') as fout:
            fout.write(response.content)
        return fn_without_path

    url = get_api_URL(ndays=ndays)
    fn_dumps,datasets = get_data(url=url, my_cb_store=cb_store_gzip)
    ###
    # extract data from parsed JSON, insert into staging table (via callback function)
    ndata_from_source=0
    for data in datasets:
        ndata_from_source += process_data(data, cb=my_row_cb)

    print('*** done processing returned data ***')
    ###
    fn_dump1 = fn_dumps[0]
    store_data_stats(cur, stg_table, filename=fn_dump1, is_scheduled=is_scheduled, ndays_req=ndays)
    ndata_merged = data_merge(cur, stg_table)

    conn.commit()
    cur.close()
    conn.close()

    print(f'row statistics: {ndata_from_source} {ndata_merged}')



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--is-scheduled', action='store_true', help='mark this run of the program as scheduled')
    parser.add_argument(
        '--ndays',
        type=float,
        required=False,
        default=10, # 10 days correspond to 960 data points (as of Feb-2026, the Hamburg IOT server limits requests to 1000 points of history)
        help=''
    )
    args = parser.parse_args()
    if not args.ndays>0:
        raise ValueError('--ndays: expecting positive value')

    main(ndays=args.ndays, is_scheduled=args.is_scheduled)
