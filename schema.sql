CREATE TABLE bikeproj_zaehlstellen(
    iot_id INT,
    name TEXT,
    longitude FLOAT,
    latitude FLOAT,
    ds_name TEXT,
    str_phenomenonTime TEXT,
    pt0 TIMESTAMP WITH TIME ZONE,
    pt1 TIMESTAMP WITH TIME ZONE,
    result INT,
    UNIQUE (iot_id,name,str_phenomenonTime)
);
