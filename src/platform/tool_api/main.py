#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module interfaces with the Open-Meteo API to obtain current temperature information
for a specified geographic location.
It utilizes the AthonTool decorator for configuration and logging setup.
"""

import datetime
import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from src.lib.package.athon.system import AthonTool


@AthonTool()
def temperature_finder(latitude: float, longitude: float) -> str:
    """
    Fetches the current temperature for specified geographic coordinates.
    Utilizes the Open-Meteo API to obtain hourly temperature data for the 
    provided latitude and longitude.
    """
    results = _get_weather_data(latitude, longitude)
    current_temperature = _find_current_temperature(results)
    return f'The current temperature is {current_temperature}°C'

def _get_weather_data(latitude: float, longitude: float) -> dict:
    tool = temperature_finder.athon_tool
    config = tool.config
    logger = tool.logger
    base_url = config["function"]["meteo_api"]
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }
    try:
        logger.debug("Fetch Temperature Data")
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
    except Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
        raise RuntimeError(f"Timeout error occurred: {timeout_err}") from timeout_err
    except RequestException as req_err:
        logger.error(f"Error during request: {req_err}")
        raise RuntimeError(f"Error during request: {req_err}") from req_err

def _find_current_temperature(weather_data: dict) -> float:
    tool = temperature_finder.athon_tool
    logger = tool.logger
    logger.debug("Search Current Temperature")
    current_utc_time = datetime.datetime.utcnow()
    time_list = [
        datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        for time_str in weather_data['hourly']['time']
    ]
    temperature_list = weather_data['hourly']['temperature_2m']
    closest_time_index = min(
        range(len(time_list)),
        key=lambda i: abs(time_list[i] - current_utc_time)
    )
    return temperature_list[closest_time_index]


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    It either prints the manifest or launches the web application
    based on the input parameter `local` : 
    - If True, the tool's manifest is printed.
    - If False, the web application is launched.
    """
    if local:
        return temperature_finder.get_manifest()
    temperature_finder.run_app()
    return None


if __name__ == "__main__":
     # Run in web application mode.
    main(False)
