""" SAM sdkit module

This scripts uses the sam sdk toolkit to simulate the performance of
a PV power plant. It uses the `sscapi.py` module that loads the
macOS SDK.

This script requires `pandas` and `numpy` to be insalled within the python
environment you are running this script

See https://sam.nrel.gov/sites/default/files/content/virtual_conf_july_2013/07-sam-virtual-conference-2013-woodcock.pdf

"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Package scripts
import sscapi
from loguru import logger
from sscapi import PySSC
from utils import timeit
from utils import _create_data_folder, get_solar_data
from utils import check_nsrdb
from nsrdb import nsrdb

# Package level variables
from utils import template_system
from context import *

ROOT = Path(__file__).parents[1]

# Module level variables
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

# logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")


def sam(lat, lng, filename, force_download, year, verbose):
    site_info = {
        "lat": lat,
        "lng": lng,
        "force_download": force_download,
        "year": str(year),
        "filename": filename,
        "verbose": verbose,
    }
    if verbose:
        pp.pprint(site_info)

    solar_data = get_nsrdb_data(**site_info)
    simulation_params = {
        "losses": 4.3,
        "dc_ac_ratio": 1.2,
        "inv_eff": 96.0,
        "system_capacity": 100,
        "verbose": False,
    }
    meta_data = nsrdb_data(meta=True, **site_info)
    simulation_params["elevation"] = meta_data["Elevation"].values
    simulation_params["timezone"] = meta_data["Time Zone"].values
    simulation_params["tilt"] = site_info["lat"]
    z = {**simulation_params, **site_info}
    sam, _ = sam_simulation(solar_data, **z)
    pass


def sam_simulation(data, meta=None, verbose=False, **kwargs):
    """SAM solar PV simulation

    Perform a PVWATTS5 simulation using some input information about the
    solar plant.

    Parameters
    ----------
        weather (pd.DataFrame): Solar radiation dataframe
        meta (pd.DataFrame): NSRDB metadata
        kwargs (dictionary): Dictionary containing simulation parameters

    Returns
    ----------
        CF (float): Capacity factor
        Generation (float): Generation over the year of simulation
        meto_data (pd.DataFrame): Dataframe with hourly generation
    """

    params = {
        "lat": kwargs["lat"],
        "lon": kwargs["lon"],
        "system_capacity": kwargs["system_capacity"],
        "dc_ac_ratio": kwargs["dc_ac_ratio"],
        "inv_eff": kwargs["inv_eff"],
        "losses": kwargs["losses"],
        "tilt": kwargs["tilt"],
        "gcr": kwargs["gcr"],
        "azimuth": kwargs["azimuth"],
        "interval": kwargs["interval"],
    }
    if verbose:
        print()
        pp.pprint({key: value for key, value in params.items()})
        print("")

    # Start sscapi module
    ssc = PySSC()
    weather_data = ssc.data_create()
    valid_keys = [
        "lat",
        "lon",
        "tz",
        "elev",
    ]
    for key, value in kwargs.items():
        bytestr = key.encode()  # Convert string to byte to read it on C
        if key in valid_keys:
            ssc.data_set_number(weather_data, bytestr, value)
    # Set tilt of system in degrees
    ssc.data_set_array(weather_data, b"year", data.index.year)
    ssc.data_set_array(weather_data, b"month", data.index.month)
    ssc.data_set_array(weather_data, b"day", data.index.day)
    ssc.data_set_array(weather_data, b"hour", data.index.hour)
    ssc.data_set_array(weather_data, b"minute", data.index.minute)
    ssc.data_set_array(weather_data, b"dn", data["DNI"])
    ssc.data_set_array(weather_data, b"df", data["DHI"])
    ssc.data_set_array(weather_data, b"wspd", data["Wind Speed"])
    ssc.data_set_array(weather_data, b"tdry", data["Temperature"])

    # Create SAM compliant object
    sam_data = ssc.data_create()
    ssc.data_set_table(sam_data, b"solar_resource_data", weather_data)
    ssc.data_free(weather_data)
    valid_keys = [
        "system_capacity",  # kW
        "dc_ac_ratio",
        "array_type",
        "inv_eff",
        "losses",
        "gcr",
        "tilt",
        "azimuth",
        "interval",
        "adjust:constant",
    ]
    for key, value in kwargs.items():
        bytestr = key.encode()  # Convert string to byte to read it on C
        if key in valid_keys:
            ssc.data_set_number(sam_data, bytestr, value)
    if kwargs["model"] == "pvwattsv7" and "module_type" in kwargs:
        ssc.data_set_number(sam_data, b"module_type", kwargs.get("module_type", 0))
    mod = ssc.module_create(kwargs.get("model").encode())

    ssc.module_exec(mod, sam_data)

    data["ac_generation_W"] = np.array(ssc.data_get_array(sam_data, b"ac"))
    data["dc_generation_W"] = np.array(ssc.data_get_array(sam_data, b"dc"))
    data["dc_capacity_factor"] = (data["dc_generation_W"] / 1e3) / kwargs[
        "system_capacity"
    ]
    data["ac_capacity_factor"] = (data["ac_generation_W"] / 1e3) / (
        kwargs["system_capacity"] / kwargs["dc_ac_ratio"]
    )
    data["POA"] = np.array(ssc.data_get_array(sam_data, b"poa"))

    # Module temperature in ºC
    data["TCell"] = np.array(ssc.data_get_array(sam_data, b"tcell"))

    logger.success(
        "SAM simulation completed. Annual capacity factor:"
        f"{data['ac_capacity_factor'].mean():.4}"
    )

    # free the memory
    ssc.data_free(sam_data)
    ssc.module_free(mod)

    return data


if __name__ == "__main__":
    PV_config = template_system()
    df, meta_data = nsrdb(verbose=True, **PV_config)
    output_ts = sam_simulation(df, verbose=True, **PV_config)
    print(
        output_ts[
            ["POA", "ac_generation_W", "dc_generation_W", "dc_capacity_factor", "TCell"]
        ].head(24)
    )
    output_ts[["ac_generation_W"]].plot()
