# Analysis of Bike Traffic in Hamburg
Table of Contents:
* Cloning the Repository
* Example: Plotting Scripts


## Cloning the Repository
The project uses a git submodule with JSON input files for testing. You only have to consider this when cloning the repository if you want to run the tests yourself. Otherwise just perform the standard `git clone` operation.

## Example: Plotting Scripts
This repository contains code for several plots showcasing what can be done with the data. See [this page](./data_observations.md) for more details.

For instance, the script `plot_radverkehr.py` plots traffic counter data loaded from the PostgreSQL database. This is a city map of Hamburg illustrating total bike counts captured by each counter on a particular day.

![bike traffic example](./doc/bikecounters.png)
