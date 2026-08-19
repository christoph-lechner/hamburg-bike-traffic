#!/bin/bash

# cron job execution starts in home directory of the user
echo "entering directory"
cd /home/bikedata/prod_bikeloader/hamburg-bike-traffic
pwd

# set up virtual environment
echo "setting up virtual environment for Python"
source /home/bikedata/prod_bikeloader/venv_prod/bin/activate
export PYTHONUNBUFFERED=1

# issue only here to avoid leaking password (for instance)
set -xe

# report git commit id
echo "git commit id:"
git log -1 --pretty=format:%H || echo "failed to determine git commit id"


python3 -m hh_bike_traffic.loader_radverkehr --is-scheduled --ndays=4
# non-zero exit code: script stops here
