import requests
import datetime
import signal
import json


### HTTP request timeouts ###
timeout_transfer = 300 # seconds, timeout for whole transfer

# Note that the following do not limit the duration of the whole transfer
timeout_connect = 30 # seconds
timeout_read = 30 # seconds (time client will wait between receiving bytes from the server, see documentation https://requests.readthedocs.io/en/latest/user/advanced/#timeouts )





# Infos about parameters in the request:
# https://fraunhoferiosb.github.io/FROST-Server/sensorthingsapi/requestingData/STA-Tailoring-Responses.html
#
# original URL (this URL is no longer up-to-date after March 2nd, 2026):
# API_URL = 'https://iot.hamburg.de/v1.1/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_HamburgerRadzaehlnetz%27%20and%20Datastreams/properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27&$count=true&$expand=Datastreams($filter=properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27;$expand=Observations($top=10;$orderby=phenomenonTime%20desc))'
#
# The original URL was modified as follows:
# 1) It does not define the sort order of the objects.
# 2) Currently there are 311 objects in total. Ask the server to deliver a maximum of 1000 objects by specifying the 'top' parameter. Then all data is obtained in a single request.

# Function to obtain URL for request (adjusts 'top' parameter)
def get_api_URL(*,ndays):
    if ndays<=0:
        raise ValueError('Illegal "ndays" value')

    from math import ceil
    nhist = ceil(24*4*ndays)
    url = f'https://iot.hamburg.de/v1.1/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_Verkehrsdaten_Rad_Infrarotdetektoren%27%20and%20Datastreams/properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27&$expand=Datastreams($filter=properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27;$expand=Observations($top={nhist};$orderby=phenomenonTime%20desc))&$count=true&$top=1000&$orderBy=@iot.id'
    print(url)
    return url


class TimeoutException(Exception):
    pass

def handler(signum, frame):
    raise TimeoutException('Total timeout for download exceeded')



def get_data(cur, stg_table, url=None, my_cb_store=None):
    tstartreq = datetime.datetime.now()
    datasets = []
    files = []
    partcntr=1
    while url:
        # Before performing the API request, install timeout. Here execution time is beyond our control (for instance, if server reacts very slowly).
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_transfer)

        try:
            # Send API request
            print('*** requesting data ***')
            response = requests.get(url, timeout=(timeout_connect,timeout_read))
            response.raise_for_status() # exception when HTTP status code is 4xx or 5xx
            print('*** request complete ***')

            # Store API response using user-provided callback function
            if my_cb_store:
                fn_without_path = my_cb_store(response=response, tstartreq=tstartreq, partcntr=partcntr)
                files.append(fn_without_path)
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

    return (files,datasets)


