import requests
import datetime



class WeatherToolbox:
    def __init__(self):
        # Coordinates for Hamburg, Germany
        self.lat, self.lon = 53.55, 10.00


    def get_weather_data(self, str_date=None, my_cb_store=None):
        if str_date is None:
            str_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')

        # here it will always be one file, but using list so that returned data structure is identical to function for bike traffic data
        files = []


        # print(str_date)
        params = {
            'date': str_date,
            'lat': self.lat,
            'lon': self.lon,
        }
        url = 'https://api.brightsky.dev/weather'
        response = requests.get(url, params=params)
        response.raise_for_status() # exception when HTTP status code is 4xx or 5xx

        if my_cb_store:
            fn_without_path = my_cb_store(response=response) # only argument: response data structure (all others are assigned in caller function)
            files.append(fn_without_path)
        data = response.json()
        datasets = [data]
        return (files,datasets)


    def process_weather_data(self, data, cb_row=None):
        # determine source describing actual measurements
        meas_source_ids=[]
        for curr_source in data['sources']:
            if curr_source['observation_type'] in ['current','historical']:
                meas_source_ids.append(curr_source['id'])


        # FIXME: The following should be replaced by better structure, such as dictionary mapping "JSON field" <-> "DB field"
        # Currently most (all?) fields have identical names, so one should add extra handling for this case.
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

            values=[self.lat,self.lon]
            for k in src_fields:
                values.append(curr_m[k])
            # print(values)
            if cb_row:
                cb_row(
                    q_all_db_fields=q_all_db_fields,
                    q_all_db_fields_placeholders=q_all_db_fields_placeholders,
                    values=values
                )
            ndata+=1
        return ndata

