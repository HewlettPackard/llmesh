#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script is designed as part of the HPE Athonet LLM Platform project
and focuses on gathering information related to Athonet API specification.
It use Athonet  OpenAPIs to get the information and ChatGPT to
synthetis them from JSON results.
"""

import sys
import asyncio
from crewai.tools import BaseTool
from src.lib.package.athon.system import Config, Logger
from src.lib.package.athon.agents import TaskForce
from src.lib.package.athon.chat import PromptRender
from src.platform.mcp.main import platform_registry
# Import tool classes needed to resolve properly the config file
from src.platform.tool_agents.openapi_tool import OpenApiManagerTool  # pylint: disable=W0611


setup = {
    "tool": {
        "module": sys.modules[__name__],
        "base_class": BaseTool
    }
}
config = Config(
    'src/platform/tool_agents/config.yaml',
    setup_parameters=setup
).get_settings()
logger = Logger().configure(config['logger']).get_logger()


async def openapi_manager(query: str) -> str:
    """
    Retrieves information from Athonet OpenAPIs based on a given question.
    This function call a Tool actions, summarize the results in a string
    """
    task_force = TaskForce.create(config['function']['multi_agents'])
    result = task_force.run(query)
    return result.completion


async def register():
    """
    Register this tool with the platform registry.
    """
    try:
        # Get tool description from prompt
        prompt = PromptRender.create(config['prompts'])
        result = prompt.load("tool_description")
        description = result.content if hasattr(result, 'content') else config["tool"]["description"]

        # Register with platform
        server = await platform_registry.register_platform_tool(
            name="tool_agents",
            func=openapi_manager,
            config=config["webapp"],
            description=description
        )
        logger.info("Tool agents service registered successfully")
        return server

    except Exception as e:
        logger.error(f"Failed to register tool agents service: {e}")
        raise


def get_manifest():
    """
    Get the tool's manifest.
    """
    # Get tool description from prompt
    prompt = PromptRender.create(config['prompts'])
    result = prompt.load("tool_description")
    description = result.content if hasattr(result, 'content') else config["tool"]["description"]

    manifest = {
        "name": "tool_agents",
        "function": "openapi_manager",
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

    # Run the server
    async def run_server():
        server = await register()
        if server:
            await server.start(
                host=config["webapp"]["ip"],
                port=config["webapp"]["port"]
            )
            logger.info(f"Tool agents server running on {config['webapp']['ip']}:{config['webapp']['port']}")
            await asyncio.Event().wait()

    asyncio.run(run_server())
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)
