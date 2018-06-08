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
import os
import click
import requests
import pandas as pd

import log
from utils import _create_data_folder, get_solar_data
from utils import timeit
from pathlib import Path
from context import *



# Module level variables
data_path.mkdir(exist_ok=True, parents=True)
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
def nsrdb(ctx, lat, lng, filename, force_download, year, verbose):
    click.secho('\nGeting data...\n', fg='blue')
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

    get_nsrdb_data(**site_info)
    pass

def get_nsrdb_data(lat, lng, year, filename=None, path=data_path,
                   force_download=False, timeseries=True,
                   meta=False,  **kwargs):
    """ Get the solar radiation data

    Args:
        lat (float): Latitude of the place
        lng (float): lnggitude of the place
        year (str): String of the year in the format '2017/'
        filename (str): Filename of the data to be downloaded
        path (str): Data path
        force_download (bool): Force download data
        timeseries (bool): Output radiation timeseries
        meta (bool): Output radiation metadata

    Returns:
        bool: Description of return value
    """
    # If you don't provide a filename choose lat and lng.
    if not filename:
        filename = f'{lat:.4f}_{lng:.4f}.csv'
        click.secho(f'\nNo filename provided. Using lat and longitude as'
                'filename', fg='yellow')
        logger.warning('No filename provided.'
                       'Using Longitude and latitude instead')
    else:
        if filename[-4:] != '.csv':
            filename = filename + '.csv'

    timeseries_path, meta_path = _create_data_folder(path, year=year)
    timeseries_path = timeseries_path.joinpath(filename)
    meta_path = meta_path.joinpath(filename)
    if kwargs['verbose']:
        click.secho(f'\nSaving data in {timeseries_path}', fg='yellow')

    if force_download or not timeseries_path.is_file():
        logger.info('Downloading timeseries')
        click.secho('Downloading timeseries from NSRDB...\n', fg='yellow')
        _ = _nsrdb_data(lng, lat, year, timeseries_path=timeseries_path,
                        meta_path=meta_path, **kwargs)
        if isinstance(_, pd.DataFrame):
            click.secho(f'Sucess ✓. Data created in {timeseries_path}\n', fg='green')
            logger.info(f'Data created in {timeseries_path}')
        else:
            click.secho(f'Failed ✘. Data download failed. Check the API',
                    fg='red')
            logger.error('Data downloading failed. Check API.')
            sys.exit(1)
    else:
        click.secho(f'Sucess ✓. File found in {timeseries_path}\n', fg='green')
        logger.info(f'File found in {timeseries_path}')

    # If you want metadata only
    if meta:
        file_path = meta_path.joinpath(filename)
        meta = pd.read_csv(meta_path)
        return (meta)

    if timeseries:
        #  data = pd.read_csv(time_series_path + filename + '.csv',  index_col=0)
        data = get_solar_data(file_path=timeseries_path)
        #  data = check_nsrdcb(data)
        return (data)


def _nsrdb_data(lng, lat, year, timeseries_path, meta_path, **kwargs):
    """ NRSDB API
    Request to the radiation data from the NSRDB API. Default columns requested.
    If needed more columns a modification to attributes variables is needed.

    Args:
        lon (float): lnggitude in degrees
        lat (float): latitude in degrees
        year (str): year in str format with a backslash at the end (2017/)
        path (str): data path
        filename (str): filename of data
        kwargs (dict): Dictionary with api_key to request data
    Returns
        pd.DataFrame: Solar radiation Time series
    """
    api_key = os.getenv('API_KEY') #kwargs['api_key'] # Personal API key

    if not api_key:
        api_key = kwargs['api_key']

    if not year == 'tmy':
        attributes = ('ghi,dhi,dni,wind_speed,wind_direction,'
                      'air_temperature,solar_zenith_angle')
    else:
        logger.info('tmy attributes')
        attributes = ('ghi,dhi,dni,wind_speed,'
                     'air_temperature')

    leap_year = 'false' # corresponding to the year above. Check here: https://kalender-365.de/leap-years.php

    utc = 'false' #This needs to be taken into account when exporting to SWITCH, as SWITCH load projections are in UTC

    # NOTE: In order to use the NSRDB data in SAM, you must specify UTC
    # as 'false'. SAM requires the data to be in the local time zone.
    url = 'http://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv'
    params = {
        'api_key': api_key,
        'wkt': f'POINT({lng:.4f} {lat:.4f})',
        'attributes': attributes,
        'email': 'mail@gmail.com',
        'name': year,
        'interval' : '60'
    }
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'cache-control': "no-cache"
    }
    response = requests.get(url, params=params, headers=headers)
    limit = int(response.headers['X-RateLimit-Remaining'])
    logger.info(f'Request limit: {limit}')
    if limit <= 10:
        logger.warning(f'You almost reach the daily limit. Be careful!')
    if response.status_code == '400':
        print (response.reason)
        print (response.content)
        sys.exit(1)

    df = pd.read_csv(response.url, header=None, index_col=[0]) # Index col to avoid deleting index columns after export
    meta = df[:2].reset_index().copy()
    meta = meta.rename(columns=meta.iloc[0]).drop(0)
    meta.to_csv(meta_path, index=False)
    time_series = df[2:].dropna(axis=1).reset_index().copy()
    time_series = time_series.rename(columns=time_series.iloc[0]).drop(0)
    time_series.to_csv(timeseries_path, index=False)

    return (time_series)

if __name__ == "__main__":
    nsrdb(obj={})
