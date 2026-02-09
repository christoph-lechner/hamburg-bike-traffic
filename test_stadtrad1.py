#!/usr/bin/env python3

# 8ef1d5ad-5e45-3f38-b639-62357fb06eed 16 Raeder
# 37a749d8-08e4-3495-a8da-1e5352d03cae 

import requests
import matplotlib.pyplot as plt

# Infos about parameters in the request:
# https://fraunhoferiosb.github.io/FROST-Server/sensorthingsapi/requestingData/STA-Tailoring-Responses.html
url = 'https://iot.hamburg.de/v1.0/Datastreams?$count=true&$filter=properties/serviceName%20eq%20%27HH_STA_StadtRad%27%20and%20properties/layerName%20eq%20%27Fahrraeder%27&$expand=Observations($select=phenomenonTime,result;$orderby=phenomenonTime%20desc;$top=10)'

stations=[]
coords=[]
cntr=1
while url:
    print('*** requesting data ***')
    response = requests.get(url)
    print(response)
    data = response.json()

    # Prepare follow-up request for next chunk of data
    #url = None
    #if '@iot.nextLink' in data:
    #    url = data['@iot.nextLink']

    # Loop over all stations in the dataset
    with open(f'log_{cntr}.txt','w') as fout:
        for station in data['value']:
            # print(f"{station['@iot.id']} {station['observedArea']['coordinates'][0]},{station['observedArea']['coordinates'][1]}")
            coords.append(station['observedArea']['coordinates'])
            stations.append(station)
            # print(f"id={station['@iot.id']} name={station['name']}")
            fout.write(f"name={station['name']}\n")
    cntr+=1

"""
for q,qq in zip(coords,stations):
    if (9.925<=q[0]) and (q[0]<=9.930) and (53.555<=q[1]) and (q[1]<=53.563):
        print(qq['Observations'])

fig,hax = plt.subplots(1)
hax.plot([_[0] for _ in coords], [_[1] for _ in coords], '+')
plt.show()
"""
