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
from nsrdb import get_nsrdb_data
from context import *


# Module level variables
data_path.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)


@click.command()
@click.option("--lat", default=19.5, prompt="Latitude", help="Latitude of the place")
@click.option("--lng", default=-99.5, prompt="Longitude", help="Longitude of the place")
@click.option("--year", default=2014, prompt="Year", help="Year of data up to 2016")
@click.option(
    "--filename",
    default=False,
    prompt="Filename",
    help="Filename of the data",
    required=False,
)
@click.option(
    "--force_download", default=False, is_flag=True, help="Force download from the API"
)
@click.option("--verbose", is_flag=True)
@click.pass_context
def nsrdb(ctx, lat, lng, filename, force_download, year, verbose):
    click.secho("\nGetting data...\n", fg="blue")

    # Define input dictionary
    site_info = {
        "lat": lat,
        "lng": lng,
        "force_download": force_download,
        "year": str(year),
        "filename": filename,
        "verbose": verbose,
    }

    if verbose:
        click.secho("+--Input data", fg="yellow")
        pp.pprint(site_info)
        print("\n")

    data = get_nsrdb_data(**site_info)

    # Print 24 hours
    print(data.head(24))

if __name__ == "__main__":
    nsrdb(obj={})
