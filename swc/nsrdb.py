"""
    Module to download data from the nsrdb from NREL.
"""

import os
import requests
import pandas as pd
import log

from utils import _create_data_folder, get_solar_data
from utils import timeit
from pathlib import Path

# Module level variables
from context import *

# Creating datafolder
data_path.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)

def nsrdb(lat, lng, year, filename=None, force_download=False, 
          verbose=False, **kwargs):
    site_info = {'lat': lat,
                 'lng': lng,
                 'force_download': force_download,
                 'year': str(year),
                 'filename': filename,
                 'verbose': verbose
                }

    # Include kwargs to dictionary
    site_info.update(kwargs)

    if verbose:
        pp.pprint(site_info)

    data = get_nsrdb_data(**site_info)

    return data

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
        logger.warning('No filename provided.'
                       'Using Longitude and latitude instead')
    else:
        # Include .csv to filename 
        if filename[-4:] != '.csv':
            filename = filename + '.csv'

    timeseries_path, meta_path = _create_data_folder(path, year=year)
    timeseries_filename = timeseries_path.joinpath(filename)
    meta_path = meta_path.joinpath(filename)

    #  if kwargs['verbose']: print(kwargs)
    #  if kwargs['verbose']:
    #      logger.warning(f'\nSaving data in {timeseries_path}')

    # If force download or file does not exists
    if force_download or not timeseries_filename.is_file():
        logger.info('Downloading timeseries from NSRCB')
        _ = request_nsrdb_data(lng, lat, year,
                timeseries_filename=timeseries_filename,
                        meta_path=meta_path, **kwargs)
        if isinstance(_, pd.DataFrame):
            logger.info(f'Data created in {timeseries_filename}')
        else:
            logger.error('Data downloading failed. Check API.')
            sys.exit(1)
    else:
        logger.info(f'File found in {timeseries_filename}')

    # If you want metadata only
    if meta:
        file_path = meta_path.joinpath(filename)
        meta = pd.read_csv(meta_path)
        return (meta)

    if timeseries:
        #  data = pd.read_csv(time_series_path + filename + '.csv',  index_col=0)
        data = get_solar_data(file_path=timeseries_filename)
        #  data = check_nsrdcb(data)
        return (data)


def request_nsrdb_data(lng, lat, year, timeseries_filename, meta_path, **kwargs):
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
    if not 'api_key' in kwargs:
        api_key = os.getenv('api_key') #kwargs['api_key'] # Personal API key
    else:
        api_key = kwargs['api_key']
    if not api_key:
        raise NameError('api_key not found. Please included it in .env or manually')


    if not year == 'tmy':
        attributes = ('ghi,dhi,dni,wind_speed,wind_direction,'
                      'air_temperature,solar_zenith_angle')
    else:
        logger.info('tmy attributes')
        attributes = ('ghi,dhi,dni,wind_speed,'
                     'air_temperature')

    leap_year = 'false' # corresponding to the year above. Check here: https://kalender-365.de/leap-years.php

    utc = 'true' #This needs to be taken into account when exporting to SWITCH, as SWITCH load projections are in UTC

    # NOTE: In order to use the NSRDB data in SAM, you must specify UTC
    # as 'false'. SAM requires the data to be in the local time zone.

    # New url to include physical model 3
    url = 'http://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv'

    params = {
        'api_key': api_key,
        'wkt': f'POINT({lng:.4f} {lat:.4f})',
        'attributes': attributes,
        'email': 'mail@gmail.com',
        'names': year,
        'interval' : '60'
    }

    params.update(kwargs)
    if kwargs['verbose']:
        pp.pprint(params)


    # headers = {
        # 'content-type': "application/x-www-form-urlencoded",
        # 'cache-control': "no-cache"
    # }

    # Make the request
    response = requests.get(url, params=params)
    logger.info(f'API Response: {response.status_code}')
    try:
        limit = int(response.headers['X-RateLimit-Remaining'])
        logger.info(f'Request limit: {limit}')
        if limit <= 10:
            logger.warning(f'You almost reach the daily limit. Be careful!')
    except KeyError:
        # TODO: Catch this error
        pass

    if response.status_code != 200:
        print (response.status_code)
        print (response.reason)
        sys.exit(1)
    else:
        df = pd.read_csv(response.url, header=None, index_col=[0]) # Index col to avoid deleting index columns after export
        meta = df[:2].reset_index().copy()
        meta = meta.rename(columns=meta.iloc[0]).drop(0)
        meta.to_csv(meta_path, index=False)
        time_series = df[2:].dropna(axis=1).reset_index().copy()
        time_series = time_series.rename(columns=time_series.iloc[0]).drop(0)

        # Remove whitespace with underscore from columns name
        time_series.columns = time_series.columns.str.replace(' ', '_')

        time_series.to_csv(timeseries_path, index=False)

        return (time_series)

if __name__ == "__main__":
    site_info = {'lat': 19.30,
                 'lng': -99,
                 'force_download': True,
                 'year': str(2014),
                 'verbose': True,
                 'interval': '60'
                }

    df = nsrdb(**site_info)
    print (df)
