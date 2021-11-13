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
# System packages
import log
import os
import pprint
from typing import Dict, Optional
from pathlib import Path

# Third-party packages
import numpy as np
import requests
import pandas as pd

# Package level variables
from context import *

# Creating datafolder
data_path.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)

def nsrdb_data(
    lat: float,
    lon: float,
    year: float,
    fname: Optional[str] = None,
    force_download: Optional[bool] = None,
    verbose: Optional[bool] = None,
    **kwargs,
) -> pd.DataFrame:
    """Get NSRDB data for a given lat, lng and year

    This function pre-process the request.

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
    # Creating dictionary to request the data
    params = {
        "lat": lat,
        "lng": lon,
        "force_download": force_download,
        "year": year,
        "fname": fname,
        "verbose": verbose,
    }

    # Include kwargs to dictionary
    params.update(kwargs)
    data = nsrdb_data_fetch(
        params, fname=fname, force_download=force_download, verbose=verbose, **kwargs
    )

    return data


def api_call(URL, params, verbose=None):
    if verbose:
        print("+ Sending following parameters to the API:\n")
        pprint.pprint(params)
        print("\n")
    response = requests.get(URL, params=params)
    logger.info(f"API Response: {response.status_code}")

    # Check if response succeded.
    if response.status_code != 200:
        # Exit program if response different from 200 and print response.
        logger.error("Data downloading failed. Check API.")
        print(response.text)
        print(response.status_code)
        print(response.reason)
        sys.exit(1)

    return response


def nsrdb_data_fetch(
    params: dict,
    data_path=data_path,
    fname: Optional[str] = None,
    force_download: Optional[bool] = None,
    verbose: Optional[bool] = None,
    timeseries=True,
    meta=False,
    **kwargs,
):
    """Downloads NSRDB data for a given latitude and longitude

    Uses an API call request_nsrdb_data if data is not found in path.

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
    if not fname:
        logger.warning(
            "No filename provided." "Using Longitude and latitude for filename instead"
        )
        fname = f"{params['year']}_{params['lng']:.4f}_{params['lat']:.4f}.csv"
    else:
        # Include .csv to filename if it does not have it.
        if fname[-4:] != ".csv":
            fname = fname + ".csv"

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
    if params.get("year") == "tmy":
        URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-tmy-download.csv"
        logger.info("tmy attributes selected")
    else:
        URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv"

    params = {
        "api_key": api_key,
        "wkt": f"POINT({params['lng']:.4f} {params['lat']:.4f})",
        # "attributes": attributes, # Default design to return all attributes
        "email": "mail@gmail.com",
        "names": params.get("year"),  # Year information
        "interval": kwargs.get("interval"),
        "utc": "false",  # By default returns local time
        "leap_year": False,  # Exclude leap day from calculation
    }
    #     # If verbose print params to request

    # Make the request
    fname = data_path.joinpath(fname)

    if force_download or not fname.is_file():
        response = api_call(URL, params, verbose=verbose)
        full_data = pd.read_csv(response.url, header=None, index_col=[0])
        full_data.to_csv(fname, index=True)
    else:
        full_data = pd.read_csv(fname,index_col=0)

    meta_data = full_data[:2].reset_index().copy()
    meta_data = (
        meta_data.rename(columns=meta_data.iloc[0]).drop(0).to_dict("records")[0]
    )

    ts_data = full_data[2:].dropna(axis=1).reset_index().copy()
    ts_data = ts_data.rename(columns=ts_data.iloc[0]).drop(0)
    ts_data["datetime"] = pd.to_datetime(ts_data[["Year", "Month", "Day", "Hour", "Minute"]])
    ts_data = ts_data.set_index("datetime")

    for column in ts_data.columns:
        ts_data[column] = ts_data[column].astype(np.float32)

    return ts_data, meta_data


if __name__ == "__main__":
    df, meta = nsrdb_data(lat=33.21, lon=-97.12, year=2012, verbose=True)
    print(df.info())
    pprint.pprint(meta)
