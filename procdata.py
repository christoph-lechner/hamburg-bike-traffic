import json
import numpy as np
from dataclasses import dataclass, asdict
from my_util import deep_get

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

    # correct API responses have element with key 'value' (and it's a 'dict')
    if not isinstance(data,dict):
        raise ValueError('data is not of type dict')
        return
    if 'value' not in data:
        print("Warning: Data does not contain object 'value'")
        return

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
        # Since 2026-03-02, the property is no longer called 'richtung', but 'direction'. We need to support both, and at least one has to be present.
        richtung = deep_get(zaehlstelle,['properties','richtung'])
        if richtung is None:
            richtung = deep_get(zaehlstelle,['properties','direction'])
            if richtung is None:
                raise ValueError('JSON data is missing expected richtung/direction') # if neither properties is present, stop processing here.

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

