import pytest
import json
from functools import partial
from procdata import process_data


# File with JSON data for tests
fn_testdata = 'hamburg-bike-traffic-testdata/dump_20260227T161613_000001.txt'

def test_emptydata():
    with pytest.raises(ValueError):
        process_data(data=None)
    with pytest.raises(ValueError):
        process_data(data=123)

    process_data(data={})



def process_data_cb_collect(obs, *, l):
    l.append(obs)

def test_procdata():
    with open(fn_testdata,'r', encoding='utf-8') as fin:
        data = json.load(fin)

    l_obs=[]
    my_cb = partial(process_data_cb_collect, l=l_obs)
    process_data(data=data, cb=my_cb)

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
