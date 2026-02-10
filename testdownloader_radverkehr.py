#!/usr/bin/env python3

import requests
import datetime
import time
import traceback

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





def get_data(url=API_URL):
    accuz = []
    coords=[]
    treq = datetime.datetime.now()
    str_treq = treq.strftime('%Y%m%dT%H%M%S')
    with open(f'out_series_radverkehr/log_{str_treq}.txt','w') as fout:
        while url:
            print('*** requesting data ***')
            response = requests.get(url)
            print(response)
            data = response.json()

            # Prepare follow-up request for next chunk of data
            url = None
            if '@iot.nextLink' in data:
                url = data['@iot.nextLink']

            # Loop over all stations in the dataset
            for zaehlstelle in data['value']:
                # workaround for first version: skip Zaehlstations that do not have coordinate type Point. This avoid coordinates such as "[9.999377, 53.580126],[9.999282, 53.580056]" (for @iot.id=5564) and help to develop the first version.
                if zaehlstelle['Datastreams'][0]['observedArea']['type']!='Point':
                    print('skipping Zaehlstation because coordinate is not of type Point')
                    continue

                curr_coords=zaehlstelle['Datastreams'][0]['observedArea']['coordinates']
                coords.append(curr_coords)
                accuz.append(zaehlstelle)
                # format most recent observation (i.e. bike traffic in last 15 minutes) into string
                str_obs="'',0"
                if 'Datastreams' in zaehlstelle:
                    if len(zaehlstelle['Datastreams'][0])>0:
                        if 'Observations' in zaehlstelle['Datastreams'][0]:
                            if len(zaehlstelle['Datastreams'][0]['Observations'])>0:
                                obs = zaehlstelle['Datastreams'][0]['Observations'][0]
                                str_obs=f"\"{obs['phenomenonTime']}\", {obs['result']}"

                fout.write(f"{zaehlstelle['@iot.id']}, {str_obs},   {curr_coords[0]},{curr_coords[1]},  \"{zaehlstelle['name']}\"\n")
    print('*** done processing request ***')
    return None


while True:
    try:
        get_data()
    except:
        # catch-all block, not best practice
        traceback.print_exc()
        pass
    time.sleep(600) # new data comes in every 900 seconds
