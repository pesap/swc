# SWC

This is a code that I wrote to make use of the System Advisor Model and the NSRDB API.

## Instalation/configuration

### Pipenv installation

In macOS

```bash
brew install pipenv
```

Install virtualenv with pipenv

```bash
pipenv install --three
```

# How to use
Using the solar radiation data as input, we implemented an easy way to change the configuration parameters to simulate the performance of a PV system.


## Configuration

First you need to get an API. Read https://developer.nrel.gov/signup/. Once you have it, create a .env file under your working folder that includes:

```yaml
API_KEY=YOUR API_KEY_GOES_HERE
```

And thats it!

## Solar radiation data

To get solar radiation data from the NSRB from a Jupyter Notebook or Console

```python
import swc.nsrdb as nsrdb
site_info = {'lat': 18.3,
             'lon': -99.3,
             'api_key':'YOUR_API_KEY',
             'force_download': False,
             'year': '2014/'}
df = nsrdb.get_nsrdb(**site_info)
```

## SAM simulation

To perform a SAM simulation using the data from the NSRDB

```python
import swc.sam_simulation as sam
simulation_params = {
    'lat': 18.3,
    'lon': -99.3
    'losses': 4.3,
    'dc_ac_ratio': 1.2,
    'inv_eff': 96.,
    'tilt': 20:,
    'sytem_capacity': 100,
    'elevation': 1100,
    'timezone': -6,
    'configuration': 0, #  0 For fixed tilt, 2 for 1-axis and 4 for 2-axis
    }

output_data, output_params = sam.sam_simulation(df, **simulation_params)
```

### LCOE Calculation

Using output_data (pd.Dataframe with hourly generation)

``` python
from src.solar import lcoe
print (lcoe(output_gen))
```


# Authors
* pesap
* Sergio Castellanos

---
## Todo
* Change the request method from the NSRDB API
* Add more inputs in performance_simulation

## Important information

I made this code for my personal use. The code merges the NSRDB-API and the SAM-SDK in one easy code. I do not own any of the above software.
If you want to know more about the [SAM-SDK](https://sam.nrel.gov/sdk) or [NSRDB-API](https://nsrdb.nrel.gov/api-instructions) please visit their respective websites.
