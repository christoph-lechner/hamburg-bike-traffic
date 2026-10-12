CREATE TABLE bikeproj_zaehlstellen(
    _h TEXT,
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
    UNIQUE (_h)
);

CREATE INDEX ON bikeproj_zaehlstellen(t_start);



CREATE TABLE bikeproj_zaehlstellen_loaderstats (
    ts_entry_creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    filename TEXT,
    is_scheduled_run BOOLEAN,
    ndays_req FLOAT,
    dataset_n_iot_ids INT,
    dataset_n_rows INT,
    dataset_min_tstart TIMESTAMP WITH TIME ZONE,
    dataset_max_tstart TIMESTAMP WITH TIME ZONE,
    dataset_min_tend TIMESTAMP WITH TIME ZONE,
    dataset_max_tend TIMESTAMP WITH TIME ZONE
);



CREATE TABLE bikeproj_weather (
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

