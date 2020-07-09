"""

"""
import os

import pandas as pd
import requests


PVWATTS_URL = "https://developer.nrel.gov/api/pvwatts/v6.json"


def request_pvwatts(
    lat,
    lon,
    year,
    system_capacity,
    module_type,
    array_type,
    tilt,
    azimuth,
    losses,
    verbose=None,
    force_download=None,
    **kwargs
):
    # TODO: Implement a better way to handle if api_key is not found.
    # Use environment variable if not found in kwargs
    if not "api_key" in kwargs:
        api_key = os.getenv("api_key")  # kwargs['api_key'] # Personal API key
    else:
        api_key = kwargs["api_key"]

    # Raise if api_key not found
    if not api_key:
        raise NameError("api_key not found. Please included it in .env or manually")

    required_parameters = {
        "lat": lat,
        "lon": lon,
        "api_key": api_key,
        "module_type": module_type,
        "system_capacity": system_capacity,  # kw
        "array_type": array_type,
        "tilt": tilt,
        "azimuth": azimuth,
        "losses": losses,
    }

    parameters = {**required_parameters, **kwargs}
    response = requests.get(PVWATTS_URL, params=parameters)

    output_data = response.json()["outputs"]

    keys = output_data.copy().keys()
    for key in keys:
        if key.endswith("_monthly"):
            output_data.pop(key)
    try:
        df = pd.DataFrame(output_data)
    except:
        return output_data
    return df


if __name__ == "__main__":
    site_info = {
        "lat": 33.21,
        "lon": -97.12,
        "module_type": 0,
        "system_capacity": 1000,  # kw
        "array_type": 0,
        "tilt": 20,
        "azimuth": 180,
        "losses": 15,
        "force_download": True,
        "year": 2011,
        "verbose": True,
        # "timeframe": "hourly",
    }
    df = request_pvwatts(**site_info)
    print(df)
