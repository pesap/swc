import sys
import time
import pandas as pd
from pathlib import Path
from context import *


data_path.mkdir(exist_ok=True, parents=True)


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time" in kw:
            name = kw.get("log_name", method.__name__.upper())
            kw["log_time"][name] = int((te - ts) * 1000)
        else:
            print("%r  %2.2f ms" % (method.__name__, (te - ts) * 1000))
        return result

    return timed


def _create_data_folder(path, source="NSRDB", year="2017"):
    """Create data folder
    Args:
    Returns:
        bool: True
    """
    TIMESERIES_DIR = path / "raw" / source / "timeseries" / year
    META_DIR = path / "raw" / source / "meta" / year
    TIMESERIES_DIR.mkdir(exist_ok=True, parents=True)
    META_DIR.mkdir(exist_ok=True, parents=True)

    return (TIMESERIES_DIR, META_DIR)


def get_solar_data(file_path=data_path, tmy=False, **kwargs):
    """Read solar data from data_path

    Read csv file and modify the custom index by a DateTimeIndex using
    columns ['Year', 'Month', 'Day', 'Hour', 'Minute']
    Args:
        path (os.PathLike): data folder direction
        filename (str): data filename inside the data folder
        tmy (str): tmy data type

    Returns
        pd.DataFrame: data with modified index
    """
    #  file_path = data_path / filename + '.csv'

    data = pd.read_csv(file_path)

    datetime_columns = ["Year", "Month", "Day", "Hour", "Minute"]

    if not "tmy" in file_path.parts:
        try:
            data.index = pd.to_datetime(data[datetime_columns])
        except TypeError:
            data.index = pd.to_datetime(data.index)
        data = data.drop(datetime_columns, axis=1)
    else:
        data.index = pd.to_datetime(data[datetime_columns])
        data = data.drop(datetime_columns, axis=1)
    return data


def check_nsrdb(data):
    """NSRDB FIX
    This function is to fix a bug that prevent to use sam.

    07/25/2017: BUG1 if DHI or any irradiation is negative the code fails.
        Temporal fix: Change negative values to 0
    """
    data = data[data["DHI"] < 0] = 0
    return data


    PV_config = {
        "losses": 14.0757,
        "dc_ac_ratio": 1.6,
        "inv_eff": 96.0,
        "system_capacity": 1000,
        "gcr": 0.4,
        "tilt": 0,
        "azimuth": 180,
        "lat": 37.77,
        "lon": -121.06,
        "year": 2012,
        "interval": 30,
        "model": "pvwattsv7",
        "module_type": 2,
        "adjust:constant": 0,
        "array_type": 2,
        "elev": 19.719999313354492,
        "tz": -8.0,
    }
def template_system():
    return {
        "losses": 14.0757,
        "dc_ac_ratio": 1.3,
        "inv_eff": 96.0,
        "system_capacity": 1000,
        "gcr": 0.4,
        "tilt": 0,
        "azimuth": 180,
        "lat": 37.77,
        "lon": -121.06,
        "year": 2012,
        "interval": 60,
        "model": "pvwattsv7",
        "module_type": 2,
        "adjust:constant": 0,
        "elev": 19.719999313354492,
        "tz": -8.0,
        "array_type": 2,  #  0 For fixed tilt, 2 for 1-axis and 4 for 2-axis
    }
