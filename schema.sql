CREATE TABLE bikeproj_zaehlstellen(
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

