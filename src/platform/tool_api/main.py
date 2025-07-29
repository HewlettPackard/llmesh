#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module interfaces with the Open-Meteo API to obtain current temperature information
for a specified geographic location.
It uses MCP for tool registration and exposure.

Updated to use the new simplified MCP architecture.
"""

import datetime
import asyncio
import httpx
from src.lib.services.core.config import Config
from src.lib.services.core.log import Logger
from src.platform.mcp.main import platform_registry
from athon.chat import PromptRender


# Load configuration
config = Config('src/platform/tool_api/config.yaml').get_settings()
logger = Logger().configure(config['logger']).get_logger()
PROMPT_CONFIG = config["prompts"]


async def temperature_finder(latitude: float, longitude: float) -> str:
    """
    Fetches the current temperature for specified geographic coordinates.
    Utilizes the Open-Meteo API to obtain hourly temperature data for the
    provided latitude and longitude.
    """
    results = await _get_weather_data(latitude, longitude)
    current_temperature = _find_current_temperature(results)
    return f'The current temperature is {current_temperature}°C'

async def _get_weather_data(latitude: float, longitude: float) -> dict:
    base_url = config["function"]["meteo_api"]
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }
    try:
        logger.debug("Fetch Temperature Data")
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        raise RuntimeError(f"HTTP error occurred: {http_err}") from http_err
    except httpx.TimeoutException as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
        raise RuntimeError(f"Timeout error occurred: {timeout_err}") from timeout_err
    except httpx.RequestError as req_err:
        logger.error(f"Error during request: {req_err}")
        raise RuntimeError(f"Error during request: {req_err}") from req_err

def _find_current_temperature(weather_data: dict) -> float:
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


async def register():
    """
    Register this tool with the platform registry.
    
    The new architecture automatically starts the server when registering.
    """
    try:
        # Get tool description from prompt
        prompt = PromptRender.create(PROMPT_CONFIG)
        result = prompt.load("tool_description")
        description = result.content if hasattr(result, 'content') else config["tool"]["description"]

        # Register with platform - server starts automatically
        server = await platform_registry.register_platform_tool(
            name="tool_api",
            func=temperature_finder,
            _config=config["webapp"],
            description=description
        )
        logger.info("Tool API service registered and started successfully")
        return server

    except Exception as e:
        logger.error(f"Failed to register tool API service: {e}")
        raise


def get_manifest():
    """
    Get the tool's manifest.
    """
    # Get tool description from prompt
    prompt = PromptRender.create(PROMPT_CONFIG)
    result = prompt.load("tool_description")
    description = result.content if hasattr(result, 'content') else config["tool"]["description"]

    manifest = {
        "name": "tool_api",
        "function": "temperature_finder",
        "description": description,
        "arguments": config["tool"]["arguments"],
        "return_direct": config["tool"]["return_direct"]
    }
    return manifest


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    It either prints the manifest or launches the web application
    based on the input parameter `local` :
    - If True, the tool's manifest is printed.
    - If False, the web application is launched.
    """
    if local:
        return get_manifest()

    # Run the server - simplified with new architecture
    async def run_server():
        # Register the tool - server starts automatically
        server = await register()
        if server:
            logger.info(f"Tool API server running on {config['webapp']['ip']}:{config['webapp']['port']}")
            # Keep the server running
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                logger.info("Shutting down Tool API server")
                # Cleanup is handled by platform registry

    asyncio.run(run_server())
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)