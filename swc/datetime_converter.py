from __future__ import division, print_function

import pandas as pd
import random
from timezonefinder import TimezoneFinder

def convert_to_local_time(row):
    """ Convert to UTC time
    # Under construction
    Args: dataframe.row
    """
    if row.timezone < 0:
        return pd.to_datetime(row.datetime).tz_localize('Etc/GMT+'+str(abs(row.timezone)))
    else:
        return pd.to_datetime(row.datetime).tz_localize('Etc/GMT-'+str(abs(row.timezone)))
    return pd.to_datetime(row.datetime).tz_localize('Etc/GMT'+str(-row.timezone))

def convert_to_mexico_time(row):
    """ Convert from UTC local time to Mexico Time.
    # Under construction!
    Args: dataframe.row
    """
    return pd.to_datetime(row.datetime_local).tz_convert('Mexico/General')

def convert_to_year(row):
    """ Temporal solution. Probably a future Bug
    # TODO: Fix to a better soluation

    Push data to be in one year only Switch requirements.

    """
    if row.datetime_mexico.year > 2014:
        return (row.datetime_mexico - pd.Timedelta(days=365))
    elif row.datetime_mexico.year < 2014:
        return (row.datetime_mexico + pd.Timedelta(days=365))
    else:
        return (row.datetime_mexico)

def get_solar_data(path, filename, *args, **kwargs):
    """ Read data from folder and process it.
    # Under construction!
    Args:
    path
    filename
    """
    data = pd.read_csv(path + filename + '.csv')
    data = data.drop(data.columns[0], axis=1)
    try:
        data.index = pd.to_datetime(data[['Year', 'Month', 'Day', 'Hour', 'Minute']], utc=True)
    except TypeError:
        data.index = pd.to_datetime(data.index)
    data = data.drop(['Year', 'Month', 'Day', 'Hour', 'Minute'], axis=1)
    data['project_name'] = filename
    data["datetime"] = data.index
    data['datetime_local'] = data.apply(convert_to_local_time, axis=1)
    data['datetime_mexico'] = data.apply(convert_to_mexico_time, axis=1)
    data['datetime_norm'] = data.apply(convert_to_year, axis=1)
    data.index = data['datetime_norm']
    data = data.sort_index()
    data['hour'] = range(1, len(data.index) + 1)
    return (data[['generation', 'hour', 'project_name']])


if __name__ == '__main__':
    directory = '../data/raw/NSRDB/'
    df = pd.read_csv('../data/interim/solar_clusters_centroids.csv')
    random = False
    grouped = df.groupby('lz')
    if random:
        df_sampled = pd.concat([d.loc[random.sample(d.index, 1)] for _, d in grouped]).reset_index(drop=True)
    else:
        #  df.itertuples() is much faster. Will change this if data gets heavy
        data_test_solar = pd.concat([get__solar_data(directory, filename)
            for filename in df['project_name']])
    data_test_solar.to_csv('solar_output.csv')
