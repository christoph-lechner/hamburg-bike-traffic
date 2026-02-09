#!/usr/bin/env python3

import requests
import matplotlib.pyplot as plt
import datetime

# Infos about parameters in the request:
# https://fraunhoferiosb.github.io/FROST-Server/sensorthingsapi/requestingData/STA-Tailoring-Responses.html
# URL copied from web browser
# API_URL = 'https://iot.hamburg.de/v1.0/Datastreams?$count=true&$filter=properties/serviceName%20eq%20%27HH_STA_StadtRad%27%20and%20properties/layerName%20eq%20%27Fahrraeder%27&$expand=Observations($select=phenomenonTime,result;$orderby=phenomenonTime%20desc;$top=10)'
#
# The original URL was modified as follows:
# 1) It does not define the sort order of the objects. Performing the identical request twice return different objects. As consequence as we navigate through the dataset using the "@iot.nextLink" (retrieving 100 objects at a time), we get some objects multiple times while not getting other objects even a single time.
# 2) Currently there are 349 objects in total. Ask the server to deliver a maximum of 500 objects by specifying the 'top' parameter. Then all data is obtained in a single request.
API_URL = 'https://iot.hamburg.de/v1.0/Datastreams?$count=true&$orderBy=name&$top=500&$filter=properties/serviceName%20eq%20%27HH_STA_StadtRad%27%20and%20properties/layerName%20eq%20%27Fahrraeder%27&$expand=Observations($select=phenomenonTime,result;$orderby=phenomenonTime%20desc;$top=10)'



def get_data(url=API_URL):
    stations=[]
    coords=[]
    cntr=1
    treq = datetime.datetime.now()
    str_treq = treq.strftime('%Y%m%dT%H%M%S')
    with open(f'out/log_{str_treq}_{cntr:06d}.txt','w') as fout:
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
            for station in data['value']:
                coords.append(station['observedArea']['coordinates'])
                stations.append(station)
                # print(f"{station['@iot.id']} {station['observedArea']['coordinates'][0]},{station['observedArea']['coordinates'][1]}")
                # format most recent observation (i.e. number of bikes available) into string
                if 'Observations' in station:
                    obs = station['Observations'][0]
                    str_obs=f"\"{obs['phenomenonTime']}\", {obs['result']}"
                else:
                    str_obs="'',0"

                fout.write(f"{station['@iot.id']}, {str_obs},   {station['observedArea']['coordinates'][0]},{station['observedArea']['coordinates'][1]},  \"{station['name']}\"\n")
    return stations,coords

stations,coords = get_data()

fig,hax = plt.subplots(1)
hax.plot([_[0] for _ in coords], [_[1] for _ in coords], '+')
plt.show()
