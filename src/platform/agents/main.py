#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module initializes an agentic tool of the platform agents service.
It utilizes the AthonTool decorator for configuration and logging setup.
"""

import os
import sys
from crewai.tools import BaseTool
from athon.agents import (
    TaskForce
)
from athon.system import (
    AthonTool,
    Config,
    Logger
)
# Import tool classes needed to resolve properly the config file
from src.platform.agents.openapi_tool import OpenApiManagerTool  # pylint: disable=W0611


# Load configuration
PATH = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(PATH, 'config.yaml')
setup = {
    "tool": {
        "module": sys.modules[__name__],
        "base_class": BaseTool
    }
}
config = Config(
    config_path,
    setup_parameters=setup
).get_settings()
# Config settings
SERVICE_CONFIG = config["service"]
PROMPT_CONFIG = config["prompts"]
LOG_CONFIG = config['logger']

# Create global objects
logger = Logger().configure(LOG_CONFIG).get_logger()


@AthonTool(config, logger)
def openapi_manager(query):
    """
    Retrieves information from Athonet OpenAPIs based on a given question.
    This function call a Tool actions, summarize the results in a string 
    """
    if not query or not isinstance(query, str):
        raise ValueError("A non-empty string query must be provided.")
    try:
        task_force = TaskForce.create(config['function']['multi_agents'])
        result = task_force.run(query)
        if not hasattr(result, 'completion') or not result.completion:
            raise RuntimeError("TaskForce did not return a valid completion.")
        return result.completion
    except Exception as e:  # pylint: disable=W0718
        # Log the error or handle it as needed
        raise RuntimeError("Failed to process query through OpenAPI manager.") from e


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    It either prints the manifest or launches the web application
    based on the input parameter `local` : 
    - If True, the tool's manifest is printed.
    - If False, the web application is launched.
    """
    if local:
        return openapi_manager.get_manifest()
    openapi_manager.run_app()
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)
