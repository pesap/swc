import sys
import log
import pandas as pd
from pathlib import Path

ROOT =  Path(__file__).parents[1]

# Module level variables
raw_path = '../data/raw/'
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True, parents=True)
logger = log.custom_logger(__name__)

def _create_data_folder(path, source='NSRDB', year='2017'):
    """ Create data folder
    Args:
    Returns:
        bool: True
    """
    TIMESERIES_DIR = DATA_DIR / 'raw' / source / 'timeseries' / year
    META_DIR = DATA_DIR / 'raw' / source / 'meta' / year
    TIMESERIES_DIR.mkdir(exist_ok=True, parents=True)
    META_DIR.mkdir(exist_ok=True, parents=True)
    return (TIMESERIES_DIR, META_DIR)

def get_solar_data(file_path=DATA_DIR,
                   tmy=False, **kwargs):
    """ Read solar data from DATA_DIR

    Read csv file and modify the custom index by a DateTimeIndex using
    columns ['Year', 'Month', 'Day', 'Hour', 'Minute']
    Args:
        path (os.PathLike): data folder direction
        filename (str): data filename inside the data folder
        tmy (str): tmy data type

    Returns
        pd.DataFrame: data with modified index
    """
    #  file_path = DATA_DIR / filename + '.csv'

    data = pd.read_csv(file_path)

    datetime_columns = ['Year', 'Month', 'Day', 'Hour', 'Minute']

    if not 'tmy' in file_path.parts:
        try:
            data.index = pd.to_datetime(data[datetime_columns])
        except TypeError:
            data.index = pd.to_datetime(data.index)
        data = data.drop(datetime_columns, axis=1)
    else:
        data.index = pd.to_datetime(data[datetime_columns])
        data = data.drop(datetime_columns, axis=1)
    return (data)

def check_nsrdb(data):
    """ NSRDB FIX
    This function is to fix a bug that prevent to use sam.

    07/25/2017: BUG1 if DHI or any irradiation is negative the code fails.
        Temporal fix: Change negative values to 0
    """
    data = data[data['DHI'] < 0] = 0
    return (data)

#  def request_data(api_key=None):
#
