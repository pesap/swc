 # -*- coding: utf-8 -*-
"""
Solar database
Example:
    Example of usage goes here

Attributes:
    module_level_variabless: None for the moment
Todo:
    * Implement multiple inputs and outputs for LCOE.
    * Clean code
"""
import sys
import numpy as np
import pandas as pd
import click
from pathlib import Path

import solar
import log
import sscapi
from utils import timeit
from utils import _create_data_folder, get_solar_data
from utils import check_nsrdb
from nsrdb import get_nsrdb_data
from context import *

ROOT =  Path(__file__).parents[1]

# Module level variables
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)


@click.command()
@click.option('--lat', default=19.5, prompt='Latitude',
                help='Latitude of the place')
@click.option('--lng', default=-99.5, prompt='Longitude',
                help='Longitude of the place')
@click.option('--year', default=2014, prompt='Year',
                help='Year of data up to 2016')
@click.option('--filename', default=False, prompt='Filename',
                help='Filename of the data', required=False)
@click.option('--force_download', default=False, is_flag=True,
                help='Force download from the API')
@click.option('--verbose', is_flag=True)
@click.pass_context
def sam(ctx, lat, lng, filename, force_download, year, verbose):
    click.secho('\nRunning SAM simulation...\n', fg='blue')
    site_info = {'lat': lat,
                 'lng': lng,
                 'force_download': force_download,
                 'year': str(year),
                 'filename': filename,
                 'verbose': verbose
                }
    if verbose:
        click.secho('Input data', fg='yellow')
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

def sam_simulation(meteo_data, verbose=False, **kwargs):
    """ SAM performance simulation

    Perform a PVWATTS simulation using the SAM python implementation.
    Args:
        meteo_data (pd.DataFrame): Solar radiation dataframe
        kwargs (dictionary): Dictionary containing simulation parameters

    Returns:
        CP (float): Capacity factor
        Generation (float): Generation over the year of simulation
        meto_data (pd.DataFrame): Dataframe with hourly generation
    """
    params = {'lat': kwargs['lat'],
              'lon': kwargs['lng'],
              'timezone': kwargs['timezone'],
              'elevation': kwargs['elevation'],
              'sys_capacity': kwargs['system_capacity'],
              'dc_ac_ratio': kwargs['dc_ac_ratio'],
              'inv_eff': kwargs['inv_eff'],
              'losses': kwargs['losses'],
              'configuration': kwargs['configuration'],
              'tilt': kwargs['tilt'],
              }

    if verbose:
        print ({key: type(value) for key, value in params.items()})

    ssc = sscapi.PySSC()
    wfd = ssc.data_create()
    ssc.data_set_number(wfd, 'lat', params['lat'])
    ssc.data_set_number(wfd, 'lon', params['lon'])
    ssc.data_set_number(wfd, 'tz', params['timezone'])
    ssc.data_set_number(wfd, 'elev', params['elevation'])
    ssc.data_set_array(wfd, 'year', meteo_data.index.year)
    ssc.data_set_array(wfd, 'month', meteo_data.index.month)
    ssc.data_set_array(wfd, 'day', meteo_data.index.day)
    ssc.data_set_array(wfd, 'hour', meteo_data.index.hour)
    ssc.data_set_array(wfd, 'minute', meteo_data.index.minute)
    ssc.data_set_array(wfd, 'dn', meteo_data['DNI'])
    ssc.data_set_array(wfd, 'df', meteo_data['DHI'])
    ssc.data_set_array(wfd, 'wspd', meteo_data['Wind Speed'])
    ssc.data_set_array(wfd, 'tdry', meteo_data['Temperature'])

    # Create SAM compliant object  
    dat = ssc.data_create()
    ssc.data_set_table(dat, 'solar_resource_data', wfd)
    ssc.data_free(wfd)

    # Set system capacity in MW
    ssc.data_set_number(dat, 'system_capacity', params['sys_capacity'])

    # Set DC/AC ratio (or power ratio). See https://sam.nrel.gov/sites/default/files/content/virtual_conf_july_2013/07-sam-virtual-conference-2013-woodcock.pdf
    ssc.data_set_number(dat, 'dc_ac_ratio', params['dc_ac_ratio'])

    # Set tilt of system in degrees
    ssc.data_set_number(dat, 'tilt', params['tilt'])

    # Set azimuth angle (in degrees) from north (0 degrees)
    ssc.data_set_number(dat, 'azimuth', 180)

    # Set the inverter efficency
    ssc.data_set_number(dat, 'inv_eff',  params['inv_eff'])

    # Set the system losses, in percent
    ssc.data_set_number(dat, 'losses', params['losses'])

    # Set ground coverage ratio
    ssc.data_set_number(dat, 'gcr', 0.4)

    # Set constant loss adjustment
    ssc.data_set_number(dat, 'adjust:constant', 0)
    system_capacity = params['sys_capacity']
    value = params['configuration']
    if isinstance(params['configuration'], dict):
        d = {}
        for key, val in value.iteritems():
            ssc.data_set_number(dat, 'array_type', val)
            # execute and put generation results back into dataframe
            mod = ssc.module_create('pvwattsv5')
            ssc.module_exec(mod, dat)
            meteo_data['generation'] = np.array(ssc.data_get_array(dat, 'gen'))
            CP = meteo_data['generation'].sum() / (525600/int('60') * system_capacity)
            generation = meteo_data['generation'].sum()
            d[key] = CP
            d['gen_'+key] = generation
        ssc.data_free(dat)
        ssc.module_free(mod)
        return (d)
    else:
        ssc.data_set_number(dat, 'array_type', value)
        # execute and put generation results back into dataframe
        mod = ssc.module_create('pvwattsv5')
        ssc.module_exec(mod, dat)
        meteo_data['generation'] = np.array(ssc.data_get_array(dat, 'gen'))
        meteo_data['cf'] = meteo_data['generation'] / system_capacity
        CP = meteo_data['generation'].sum() / (525600/int('60') * system_capacity)
        generation = meteo_data['generation'].sum()
        click.secho('Output data from SAM.', fg='green')
        click.secho(f'Capacity Factor: {CP}', fg='blue')
        click.secho(f'Annual Generation: {generation}', fg='blue')
        ssc.data_free(dat)
        ssc.module_free(mod)
        meteo_data.to_csv(output_path / 'test.csv')
        return (meteo_data, (CP, generation))
    return (True)


if __name__ == "__main__":
    site_info = {'lat': 19.3,
                 'lng': -99.3,
                 'force_download': False,
                 'year': '2014'
                }

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
