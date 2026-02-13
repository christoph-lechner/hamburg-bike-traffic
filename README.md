## Data Observations
* The default URLs for data requests to the Hamburg IOT server do not specify the `orderBy` parameter. This results in what appears to be random data ordering (you can verify by repeating the same request after some time). When the server is only returning a part of the entire dataset (by default, 100 elements, use the `top` parameter the change this), it is critical that the data is not random. This was addressed by specifying `orderBy=name` (a parameter that does not depend on the actual data values) and, to accelerate data transfer, `top=500` to get all data in a single response.
* The station reported as `@iot.id=25605` sometimes has geographical coordinates0,0. Before plotting the data, datapoints with coordinates 0,0 are rejected 

## Plotting the Data
The script `plot_radverkehr.py` plots bike counter data loaded from the PostgreSQL database.

One can totalize for each counter the total number of bikes registered on a particular day.

![bike traffic](./bikecounters.png)

It is also possible to compute for every 15-minute interval the total number of bikes registered at the counters. (Note that it is possible that a single bike rider is registered multiple times.) On Friday, Feb-13, the weather in Hamburg was snowy, which could explain the lower numbers.

![bike traffic](./biketraffic.png)


The script `plot_stadtrad.py` currently contains code to indicate the positions of the StadtRad stations that are contained in a CSV file.

![stadtrad stations](./stadtrad_stations.png)
