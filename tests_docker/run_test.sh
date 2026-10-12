#!/usr/bin/env bash

env HH_BIKE_TRAFFIC_PG_DSN="postgres://testuser:testpwd@127.0.0.1:5432/testdb" python3 -m hh_bike_traffic.test_html_report
