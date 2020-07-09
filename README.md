<img src="./docs/logo.png" alt="SWC" align="left" width="192px" height="192px"/>
<img align="left" width="0" height="192px" hspace="10"/>

#### SWC 
> Simplified solar performance simulator

[![MIT License](https://img.shields.io/badge/license-MIT-007EC7.svg?style=flat-square)](/LICENSE) [![GitHub last commit](https://img.shields.io/github/last-commit/pesap/swc?style=flat-square)](https://github.com/pesap/swc/commits/main) [![Version](https://img.shields.io/github/v/tag/pesap/swc?style=flat-square)](https://img.shields.io/github/v/tag/pesap/swc?style=flat-square) [![PyPI](https://img.shields.io/pypi/v/swc?style=flat-square)](https://pypi.org/project/swc/)

<br/>


## Table of contents
* [About](#about)
* [Installation](#installation)
* [How to use](#howtouse)
    * [Configuration](#configuration)
    * [Solar radiation data](#solarradiationdata)
    * [SAM simulation](#samsimulation)
* [Authors](#authors)

## About

I made this code for my personal use. The code merges the NSRDB-API and the SAM-SDK in one easy code to simulate the performance
of a solar power plant at a given location. If you want to know more about the [SAM-SDK](https://sam.nrel.gov/sdk) or [NSRDB-API](https://nsrdb.nrel.gov/api-instructions) please visit their respective websites.


## Installations

To install using `pip`

```bash
pip install swc
```

To upgrade

```bash
pip install --upgrade swc
```

## How to use
Using the solar radiation data as input, we implemented an easy way to change the configuration parameters to simulate the performance of a PV system.


### Configuration

First you need to get an API. Read https://developer.nrel.gov/signup/. Once you have it, create a .env file under your working folder that includes:

```yaml
API_KEY=YOUR API_KEY_GOES_HERE
```

And thats it!

### Solar radiation data

To get solar radiation data from the NSRB from a Jupyter Notebook or Console

```python
import swc.nsrdb as nsrdb

# Define site dictionary
site_info = {
    "lat": 18.3,
    "lng": -99.3,
    "api_key": "YourAPIKEY",
    "force_download": False,
    "year": "2014",
}

# Download data
df = nsrdb.get_nsrdb_data(**site_info)
print(df.head())
```

### SAM simulation

To perform a SAM simulation using the data from the NSRDB

```python
import swc.sam_simulation as sam

# Define simulation params
simulation_params = {
    "lat": site_info["lat"],
    "lng": site_info["lng"],
    "losses": 4.3,
    "dc_ac_ratio": 1.2,
    "inv_eff": 96.0,
    "tilt": 20,
    "system_capacity": 100,
    "elevation": 1100,
    "timezone": -6,
    "configuration": 0,  #  0 For fixed tilt, 2 for 1-axis and 4 for 2-axis
    "gcr": 0.4,
    "azimuth": 100,
    "interval": 60,
}

# Run SAM simulation
output_data, output_params = sam.sam_simulation(df, **simulation_params)

print(output_data.head())
```


## Authors
* pesap
* Sergio Castellanos

---

## Todo

- [ ] Update the code to include more use cases.

