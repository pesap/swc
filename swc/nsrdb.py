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
import requests
import pandas as pd

import log
from utils import _create_data_folder, get_solar_data
from pathlib import Path

ROOT =  Path(__file__).parents[1]

# Module level variables
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)

def get_nsrdb_data(lat, lng, year, filename=None, path=DATA_DIR,
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

    timeseries_path, meta_path = _create_data_folder(path, year=year)

    # If you don't provide a filename choose lat and lng.
    if not filename:
        filename = f'{lat:.4f}_{lng:.4f}.csv'
        logger.warning('No filename provided.'
                       'Using Longitude and latitude instead')
    else:
        if filename[-4:] != '.csv':
            filename = filename + '.csv'

    file_path = timeseries_path.joinpath(filename)

    if force_download or not file_path.is_file():
        logger.info('Downloading timeseries')
        _ = _nsrdb_data(lng, lat, year, path=file_path,
                        filename=filename, **kwargs)
        if isinstance(_, pd.DataFrame):
            logger.info(f'Data created in {file_path}')
        else:
            logger.error('Data downloading failed. Check API.')
            sys.exit(1)
    else:
        logger.info(f'File found in {file_path}')

    # If you want metadata only
    if meta:
        file_path = meta_path.joinpath(year, filename)
        meta = pd.read_csv(file_path)
        return (meta)

    if timeseries:
        #  data = pd.read_csv(time_series_path + filename + '.csv',  index_col=0)
        data = get_solar_data(file_path=file_path)
        #  data = check_nsrdcb(data)
        return (data)


def _nsrdb_data(lng, lat, year, path, filename, **kwargs):
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
    if response.status_code == '400':
        print (response.reason)
        print (response.content)
        sys.exit(1)

    df = pd.read_csv(response.url, header=None, index_col=[0]) # Index col to avoid deleting index columns after export
    #  logger(e)
    #  logger.error('Could not read data directly from API.')
    meta = df[:2].reset_index().copy()
    meta = meta.rename(columns=meta.iloc[0]).drop(0)
    #  meta.to_csv(path + year + '/meta/' + filename + '.csv')
    time_series = df[2:].dropna(axis=1).reset_index().copy()
    time_series = time_series.rename(columns=time_series.iloc[0]).drop(0)
    time_series.to_csv(path, index=False)

    return (time_series)

if __name__ == "__main__":
    site_info = {'lat': 19.3,
                 'lng': -99.3,
                 'force_download': True,
                 'year': '2014'
                }

    df = get_nsrdb_data(**site_info)
