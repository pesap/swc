""" NSRDB data module

This script downloads the data from the NSRDB from NREL for a specific
location in the world. This toolfunction with an input dictionary with
the parameters to request the data.

This script requires `pandas` and `request` to be insalled within the python
environment you are running this script

TODO:
    * Change way to handle timeseries_path and meta_path
    * Catch different errors from request
    * Implement a better way to debug
"""

import os
import log
import requests
import pandas as pd
from pathlib import Path

# Package scripts
from utils import _create_data_folder, get_solar_data
from utils import timeit

# Package level variables
from context import *

# Creating datafolder
data_path.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)


def nsrdb(lat, lng, year, filename=None, force_download=False, verbose=False, **kwargs):
    """ NSRDB data

    This function pre-process the request.

    NOTE: This function might change in the future
    Parameters
    ----------
        lat (float):
            Latitude in degrees
        lng (float):
            Longtitude in degrees
        year (str):
            Year of data
        filename (str): optional
            Filename of the data
        force_download (bool): optional
            Force the data to be download. Otherwise look for data in folder.
        verbose (bool): optional
            Print dictionaries
        kwargs (dict):
            Dictionary with api_key to request data

    Returns
    -------
        data (pd.DataFrame):
            Radiation dataDescription of return value
    """
    site_info = {
        "lat": lat,
        "lng": lng,
        "force_download": force_download,
        "year": str(year),
        "filename": filename,
        "verbose": verbose,
    }

    # Include kwargs to dictionary
    site_info.update(kwargs)

    if verbose:
        pp.pprint(site_info)

    data = get_nsrdb_data(**site_info)

    return data


def get_nsrdb_data(
    lat,
    lng,
    year,
    filename=None,
    path=data_path,
    force_download=False,
    timeseries=True,
    meta=False,
    **kwargs,
):
    """ Get the solar radiation data

    Calls request_nsrdb_data if data is not found in path.

    Parameters
    ----------
        lat (float):
            Latitude in degrees
        lng (float):
            Longtitude in degrees
        year (str):
            Year of data
        filename (str): optional
            Filename of the data
        path (os.PathLike):
            Path to save the data
        force_download (bool): optional
            Force the data to be download. Otherwise look for data in folder.
        timeseries (bool): optional
            false or true for returing timeseries data
        meta (bool): optional
            false or true for returing meta data
        kwargs (dict):
            Dictionary with api_key to request data

    Returns
    -------
        bool: Description of return value
    """

    # If you don't provide a filename use lat and lng.
    if not filename:
        filename = f"{lat:.4f}_{lng:.4f}.csv"
        logger.warning(
            "No filename provided." "Using Longitude and latitude for filename instead"
        )
    else:
        # Include .csv to filename if it does not have it.
        if filename[-4:] != ".csv":
            filename = filename + ".csv"

    timeseries_path, meta_path = _create_data_folder(path, year=year)
    timeseries_filename = timeseries_path.joinpath(filename)
    meta_path = meta_path.joinpath(filename)

    #  if kwargs['verbose']: print(kwargs)
    #  if kwargs['verbose']:
    #      logger.warning(f'\nSaving data in {timeseries_path}')

    # If force download or file does not exists
    if force_download or not timeseries_filename.is_file():
        logger.info("Downloading timeseries from NSRDB.")
        request_nsrdb_data(
            lat,
            lng,
            year,
            timeseries_filename=timeseries_filename,
            meta_path=meta_path,
            **kwargs,
        )
        logger.info(f"Data created in {timeseries_filename}")
    else:
        logger.info(f"File found in {timeseries_filename}")

    # If you want metadata only
    if meta:
        file_path = meta_path.joinpath(filename)
        meta = pd.read_csv(meta_path)
        return meta

    if timeseries:
        #  data = pd.read_csv(time_series_path + filename + '.csv',  index_col=0)
        data = get_solar_data(file_path=timeseries_filename)
        #  data = check_nsrdcb(data)
        return data


def request_nsrdb_data(
    lat,
    lng,
    year,
    timeseries_filename,
    meta_path,
    utc="false",
    leap_year="false",
    interval=60,
    **kwargs,
):
    """ NRSDB request function

    Request the radiation data from the NSRDB API. Default columns requested.

    If needed more columns a modification to attributes variables is needed.

    UTC by default is false because if the data is going to be used with SAM
    it needs to be in the local time zone. If used with SWITCH needs to be true
    because switch load projections are in UTC.

    Parameters
    ----------
        lat (float):
            Latitude in degrees
        lng (float):
            Longtitude in degrees
        year (str):
            Year of data
        timeseries_filename (str):
            Filename of the timeseries data
        meta_path (str):
            Folder path of the meta data
        utc (str): optional
            false or true for utc time data
        leap_year (str): optional
            Corresponding to the year above
        interval (str): optional
            This value determines data resolution. Either 30 minute or 60
            minute intervals are available.
        kwargs (dict):
            Dictionary with api_key to request data

    Returns
    ----------
        nothing
    """

    # TODO: Implement a better way to handle if api_key is not found.
    # Use environment variable if not found in kwargs
    if not "api_key" in kwargs:
        api_key = os.getenv("api_key")  # kwargs['api_key'] # Personal API key
    else:
        api_key = kwargs["api_key"]

    # Raise if api_key not found
    if not api_key:
        raise NameError("api_key not found. Please included it in .env or manually")

    # TODO: Include more attributes using kwargs.
    if not year == "tmy":
        attributes = (
            "clearsky_dhi,",
            "clearsky_dni,",
            "clearsky_ghi,",
            "ghi,dhi,dni,wind_speed,wind_direction,"
            "air_temperature,solar_zenith_angle",
        )
    else:
        logger.info("tmy attributes selected")
        attributes = "ghi,dhi,dni,wind_speed," "air_temperature"

    # New url to include physical model 3
    url = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv"

    params = {
        "api_key": api_key,
        "wkt": f"POINT({lng:.4f} {lat:.4f})",
        #"attributes": attributes, # I comment this one to return all
        "email": "mail@gmail.com",
        "names": year,  # Year information
        "interval": str(interval),
        "utc": utc,
        "leap_year": leap_year,
    }

    # Include kwargs in the params
    params.update(kwargs)

    # If verbose print params to request
    if "verbose" in kwargs:
        pp.pprint(params)

    # TODO: Check if the code below is mandatory to make the request.
    # headers = {
    # 'content-type': "application/x-www-form-urlencoded",
    # 'cache-control': "no-cache"
    # }

    # Make the request
    response = requests.get(url, params=params)
    logger.info(f"API Response: {response.status_code}")
    try:
        #  Check if limit in response headers
        limit = int(response.headers["X-RateLimit-Remaining"])
        logger.info(f"Request limit: {limit}")
        if limit <= 10:
            logger.warning(f"You almost reach the daily limit. Be careful!")
    except KeyError:
        #  TODO: Catch this error
        pass

    # Check if response succeded.
    if response.status_code != 200:
        # Exit program if response different from 200 and print response.
        logger.error("Data downloading failed. Check API.")
        print(response.text)
        print(response.status_code)
        print(response.reason)
        sys.exit(1)
    else:
        # Read data from response with index col to avoid deleting index
        # after exporting
        data = pd.read_csv(response.url, header=None, index_col=[0])

        # Get the metadata from data
        meta = data[:2].reset_index().copy()
        meta = meta.rename(columns=meta.iloc[0]).drop(0)
        meta.to_csv(meta_path, index=False)

        # Get the timeseries from data
        time_series = data[2:].dropna(axis=1).reset_index().copy()
        time_series = time_series.rename(columns=time_series.iloc[0]).drop(0)
        time_series.to_csv(timeseries_filename, index=False)


if __name__ == "__main__":
    site_info = {
        "lat": 33.21,
        "lng": -97.12,
        "force_download": True,
        "year": str(2012),
        "verbose": True,
        "interval": 60,
    }

    df = nsrdb(**site_info)
    print(df.head())

