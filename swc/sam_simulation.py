""" SAM sdkit module

This scripts uses the sam sdk toolkit to simulate the performance of
a PV power plant. It uses the `sscapi.py` module that loads the
macOS SDK.

This script requires `pandas` and `numpy` to be insalled within the python
environment you are running this script

TODO:


See https://sam.nrel.gov/sites/default/files/content/virtual_conf_july_2013/07-sam-virtual-conference-2013-woodcock.pdf

"""

import sys
import log
import numpy as np
import pandas as pd
from pathlib import Path

# Package scripts
import sscapi
from utils import timeit
from utils import _create_data_folder, get_solar_data
from utils import check_nsrdb
from nsrdb import nsrdb
from nsrdb import get_nsrdb_data

# Package level variables
from context import *

ROOT =  Path(__file__).parents[1]

# Module level variables
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)

def default_sam_params():
    return ({
            'losses': 14.0757,
            'dc_ac_ratio': 1.1,
            'inv_eff': 96.,
            'system_capacity': 100,
            'configuration': 0, #  0 For fixed tilt, 2 for 1-axis and 4 for 2-axis
            'verbose': False,
            'gcr': 0.4,
            'tilt': 25,
            'azimuth':100}
            )


def sam(lat, lng, filename, force_download, year, verbose):
    site_info = {'lat': lat,
                 'lng': lng,
                 'force_download': force_download,
                 'year': str(year),
                 'filename': filename,
                 'verbose': verbose
                }
    if verbose:
        pp.pprint(site_info)

    solar_data = get_nsrdb_data(**site_info)
    simulation_params = {
                            'losses': 4.3,
                            'dc_ac_ratio': 1.2,
                            'inv_eff': 96.,
                            'system_capacity': 100,
                            'configuration': 2, #  0 For fixed tilt, 2 for 1-axis and 4 for 2-axis
                            'verbose': False}
    meta_data = get_nsrdb_data(meta=True, **site_info)
    simulation_params['elevation'] = meta_data['Elevation'].values
    simulation_params['timezone'] = meta_data['Time Zone'].values
    simulation_params['tilt'] = site_info['lat']
    z = {**simulation_params, **site_info}
    sam, _ = sam_simulation(solar_data, **z)
    pass

def sam_simulation(data, verbose=False, **kwargs):
    """ SAM solar PV simulation

    Perform a PVWATTS5 simulation using some input information about the
    solar plant.

    Parameters
    ----------
        data (pd.DataFrame): Solar radiation dataframe
        kwargs (dictionary): Dictionary containing simulation parameters

    Returns
    ----------
        CP (float): Capacity factor
        Generation (float): Generation over the year of simulation
        meto_data (pd.DataFrame): Dataframe with hourly generation
    """

    params = {'lat': kwargs['lat'],
              'lng': kwargs['lng'],
              'timezone': kwargs['timezone'],
              'elevation': kwargs['elevation'],
              'system_capacity': kwargs['system_capacity'],
              'dc_ac_ratio': kwargs['dc_ac_ratio'],
              'inv_eff': kwargs['inv_eff'],
              'losses': kwargs['losses'],
              'configuration': kwargs['configuration'],
              'tilt': kwargs['tilt'],
              'gcr': kwargs['gcr'],
              'azimuth': kwargs['azimuth'],
              'interval': kwargs['interval'],
              }

    if verbose:
        print ({key: value for key, value in params.items()})

    # Start sscapi module
    ssc = sscapi.PySSC()
    wfd = ssc.data_create()
    ssc.data_set_number(wfd, 'lat', params['lat'])
    ssc.data_set_number(wfd, 'lon', params['lng'])
    ssc.data_set_number(wfd, 'tz', params['timezone'])
    ssc.data_set_number(wfd, 'elev', params['elevation'])
    ssc.data_set_array(wfd, 'year', data.index.year)
    ssc.data_set_array(wfd, 'month', data.index.month)
    ssc.data_set_array(wfd, 'day', data.index.day)
    ssc.data_set_array(wfd, 'hour', data.index.hour)
    ssc.data_set_array(wfd, 'minute', data.index.minute)
    ssc.data_set_array(wfd, 'dn', data['DNI'])
    ssc.data_set_array(wfd, 'df', data['DHI'])
    ssc.data_set_array(wfd, 'wspd', data['Wind Speed'])
    ssc.data_set_array(wfd, 'tdry', data['Temperature'])

    # Create SAM compliant object  
    dat = ssc.data_create()
    ssc.data_set_table(dat, 'solar_resource_data', wfd)
    ssc.data_free(wfd)

    # Set system capacity in MW
    ssc.data_set_number(dat, 'system_capacity', params['system_capacity'])

    # Set DC/AC ratio (or power ratio).     
    ssc.data_set_number(dat, 'dc_ac_ratio', params['dc_ac_ratio'])

    # Set tilt of system in degrees
    ssc.data_set_number(dat, 'tilt', params['tilt'])

    # Set azimuth angle (in degrees) from north (0 degrees)
    ssc.data_set_number(dat, 'azimuth',params['azimuth'])

    # Set the inverter efficency
    ssc.data_set_number(dat, 'inv_eff',  params['inv_eff'])

    # Set the system losses, in percent
    ssc.data_set_number(dat, 'losses', params['losses'])

    # Set ground coverage ratio
    ssc.data_set_number(dat, 'gcr', params['gcr'])

    # Set constant loss adjustment
    ssc.data_set_number(dat, 'adjust:constant', 0)
    # system_capacity = params['sys_capacity']
    # value = params['configuration']
    ssc.data_set_number(dat, 'array_type', params['configuration'])

    mod = ssc.module_create('pvwattsv5')
    ssc.module_exec(mod, dat)

    # System AC generation
    data['ac_generation'] = np.array(ssc.data_get_array(dat, 'ac'))
    data['dc_generation'] = np.array(ssc.data_get_array(dat, 'dc'))
    data['generation'] = np.array(ssc.data_get_array(dat, 'gen'))

    # Plane of array (POA) irradiance in kWh
    data['POA'] = np.array(ssc.data_get_array(dat, 'poa'))

    # Module temperature in ºC
    data['TCell'] = np.array(ssc.data_get_array(dat, 'tcell'))

    capacity_factor = ssc.data_get_number(dat, 'capacity_factor')
    total_energy = ssc.data_get_number(dat, 'annual_energy')

    # free the memory
    ssc.data_free(dat)
    ssc.module_free(mod)

    # TODO: Check if this functionallity is what I want to implement as 
    # Standard

    # if isinstance(params['configuration'], dict):
        # d = {}
        # for key, val in value.iteritems():
            # ssc.data_set_number(dat, 'array_type', val)
            # # execute and put generation results back into dataframe
            # mod = ssc.module_create('pvwattsv5')
            # ssc.module_exec(mod, dat)
            # data['generation'] = np.array(ssc.data_get_array(dat, 'gen'))
            # CP = data['generation'].sum() / (525600/int('60') * system_capacity)
            # generation = data['generation'].sum()
            # d[key] = CP
            # d['gen_'+key] = generation
        # ssc.data_free(dat)
        # ssc.module_free(mod)
        # return (d)
    # else:
        # ssc.data_set_number(dat, 'array_type', value)
        # # execute and put generation results back into dataframe
        # mod = ssc.module_create('pvwattsv5')
        # ssc.module_exec(mod, dat)
        # data['generation'] = np.array(ssc.data_get_array(dat, 'gen'))
        # data['cf'] = data['generation'] / system_capacity
        # CP = data['generation'].sum() / (525600/int('60') * system_capacity)
        # generation = data['generation'].sum()
        # ssc.data_free(dat)
        # ssc.module_free(mod)
        # data.to_csv(output_path / 'test.csv')
        # return (data, (CP, generation))

    return (data, (capacity_factor, total_energy))


if __name__ == "__main__":
    site_info = {'lat': 33.21,
                 'lng': -97.12,
                 'force_download': False,
                 'year': str(2012),
                 'verbose': True,
                 'interval': 60
                }
    df = nsrdb(**site_info)
    meta_data = get_nsrdb_data(meta=True, **site_info)
    simulation_params = default_sam_params()
    simulation_params['elevation'] = meta_data['Elevation'].values
    simulation_params['timezone'] = meta_data['Time Zone'].values
    simulation_params['tilt'] = site_info['lat']

    # Include lat and lng to simulation params
    simulation_params.update(site_info)
    results, _ = sam_simulation(df, **simulation_params)
    print (results[['ac_generation', 'dc_generation', 'TCell']].head(24))
