# Analysis of Bike Traffic in Hamburg
Table of Contents:
* [Installation](#installation)
* [Example: Plotting Scripts](#example-plotting-scripts)

## Installation
The following steps are needed to prepare your installation of this project

### Clone the Repository
This project uses a git submodule to provide JSON input files for testing. You only have to consider this if you want to run these tests yourself. Otherwise just perform the standard `git clone` operation.

### Create the tables using the schema
Use the commands in file `schema.sql` in this repository.

### Adjust the DB Connection parameters
The connection parameters to connect to the PostgreSQL database server have to be adjusted in `db_conn.py`. (To facilitate deployment via Docker, it is planned to provide these in the future via environment variables.)

As usually, the password is to be provided in `~/.pgpass` file (don't forget to set mode 0600, otherwise the file will be ignored).

To verify that everything is correctly set up, you can run the simple test script `check_db_conn.py`.

### Manually run data ingestion script
Manually run the script `loader_radverkehr.py`.

### Install data ingestion script as cronjob
A possible configuration looks like this:
```
0 4 * * * /home/johndoe/prod/bikeproj/loader_radverkehr.py --is-scheduled --ndays=4
```
This runs every day at 4am and fetches 4 days worth of data from the API server.

## Example: Plotting Scripts
This repository contains code for several plots showcasing what can be done with the data. See [this page](./data_observations.md) for more details.

For instance, the script `plot_radverkehr.py` plots traffic counter data loaded from the PostgreSQL database. This is a city map of Hamburg illustrating total bike counts captured by each counter on a particular day.

![bike traffic example](./doc/bikecounters.png)
