import pytest
import json
from functools import partial
from procdata import process_data


def test_emptydata():
    with pytest.raises(ValueError):
        process_data(data=None)
    with pytest.raises(ValueError):
        process_data(data=123)

    process_data(data={})



def process_data_cb_collect(obs, *, l):
    l.append(obs)

def load_obs(fn):
    with open(fn,'r', encoding='utf-8') as fin:
        data = json.load(fin)

    l_obs=[]
    my_cb = partial(process_data_cb_collect, l=l_obs)
    process_data(data=data, cb=my_cb)
    return l_obs

def test_procdata():
    # File with JSON data for tests
    fn_testdata = 'hamburg-bike-traffic-testdata/dump_20260227T161613_000001.txt'

    l_obs = load_obs(fn_testdata)

    # iot_id=11796: No observations for this one in the testdata
    # -> means that it must not show up in the list of observations
    for obs in l_obs:
        if obs.iot_id==11796:
                raise ValueError('For test data: iot_id=11796 has not observations -> it should not show up in extracted observations')

    # iot_id=5627: this is one of those with spcial handing due to LineString coordinates
    got_it=False
    for obs in l_obs:
        if obs.iot_id==5627:
            if obs.remark is None:
                raise ValueError('For test data: Expecting remarks for iot_id=5627')
            else:
                got_it=True
                break

    # For any 'standard' Zaehlstelle, there should be 1000 observations
    # -> test it for one
    cntr_expected=1000
    cntr=0
    for obs in l_obs:
        if obs.iot_id==5570:
            cntr+=1
    assert cntr==cntr_expected, f'For test data: Expecting {cntr_expected} observations for a Zaehlstelle, got {cntr}'




def test_procdata_check_values(capsys):
    """
    Verify that function correctly extracts values from JSON file
    """
    # File with JSON data for tests
    fn_testdata = 'hamburg-bike-traffic-testdata/dump_20260227T161613_000001.txt'

    l_obs = load_obs(fn_testdata)

    """
    with capsys.disabled():
        print(l_obs[1])
    """

    o = l_obs[1]
    assert o.iot_id==5570 # iot_id of the station (the datastream has another iot_id)
    assert o.pt_split0=='2026-02-27T14:30:00Z' # still a string
    assert o.pt_split1=='2026-02-27T14:44:59Z' # still a string
    assert o.result==104



def test_procdata3():
    """
    Test with malformatted data set. One of the counter stations does not have a 'direction' property (it was renamed). We expect the function to raise an exception.
    """
    fn_testdata = 'hamburg-bike-traffic-testdata/dump_20260304T220911_000001.test_missing_direction'

    with pytest.raises(ValueError):
        l_obs = load_obs(fn_testdata)
