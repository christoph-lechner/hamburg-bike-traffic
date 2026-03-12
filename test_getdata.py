from getdata import get_data,get_api_URL

def test_get_api_URL():
    # is a URL generated without errors?
    url = get_api_URL(ndays=3)
    assert isinstance(url,str)

# 2026-03-12, CL
# Test outcome of function get_data would depend on result of API request -- something we do not control.
# For instance, an exception results from 404 errors.
# -> not testing at the moment.
#
# Possible workaround would be to host a small, static JSON file on a dedicated webspace.
