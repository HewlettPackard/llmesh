#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script is designed as part of the HPE Athonet LLM Platform project 
and focuses on gathering information related to Athonet API specification.
It use Athonet  OpenAPIs to get the information and ChatGPT to 
synthetis them from JSON results.
"""

import sys
from crewai.tools import BaseTool
from src.lib.package.athon.system import AthonTool, Config, Logger
from src.lib.package.athon.agents import TaskForce
# Import tool classes needed to resolve properly the config file
from src.platform.agents.openapi_tool import OpenApiManagerTool  # pylint: disable=W0611


setup = {
    "tool": {
        "module": sys.modules[__name__],
        "base_class": BaseTool
    }
}
config = Config(
    'src/platform/agents/config.yaml',
    setup_parameters=setup
).get_settings()
logger = Logger().configure(config['logger']).get_logger()


@AthonTool(config, logger)
def openapi_manager(query):
    """
    Retrieves information from Athonet OpenAPIs based on a given question.
    This function call a Tool actions, summarize the results in a string 
    """
    task_force = TaskForce.create(config['function']['multi_agents'])
    result = task_force.run(query)
    return result.completion


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
