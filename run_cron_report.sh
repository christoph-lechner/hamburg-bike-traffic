#!/bin/bash

# cron job execution starts in home directory of the user
echo "entering directory"
# cd /home/bikedata/prod_bikeloader/hamburg-bike-traffic
pwd

# Load configuration parameters
# RSYNC_DEST defines the destination of the data transfer.
source ./run_cron_report.cfg

if [[ ! -v RSYNC_DEST ]]; then
	echo "You must define variable RSYNC_DEST"
	exit 1
fi

# set up virtual environment
echo "setting up virtual environment for Python"
# source /home/bikedata/prod_bikeloader/venv_prod/bin/activate
export PYTHONUNBUFFERED=1

# issue only here to avoid leaking password (for instance)
set -xe

# report git commit id
echo "git commit id:"
git log -1 --pretty=format:%H || echo "failed to determine git commit id"


# run with relative path, to make sure we are in the correct working directory
./generate_html_report.py

rsync -avc -i --stats --timeout=60 -e "ssh -l bikeproj" ./report/ $RSYNC_DEST
