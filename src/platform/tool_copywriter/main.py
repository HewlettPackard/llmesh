#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module initializes an application that improve a text 
acting as an expert copywriter.
It utilizes the AthonTool decorator for configuration and logging setup.
"""

from langchain.schema import HumanMessage, SystemMessage
from libs.chat.model import ChatModel
from libs.system_services.tool_client import AthonTool
from libs.core.config import Config
from libs.core.log import Logger


# Parse command-line arguments and start the application
config = Config('src/platform/tool_copywriter/config.yaml').get_settings()
# Config settings
FUNCTION_CONFIG = config["function"]
PROMPT_CONFIG = config["prompts"]
LOG_CONFIG = config['logger']
# Create Logger
logger = Logger().configure(LOG_CONFIG).get_logger()


@AthonTool(config, logger)
def basic_copywriter(input_string: str) -> str:
    """
    Improve the text using the LLM as an expert copywriter
    """
    # Log info of function
    logger.info("Tool BasicCopywriter started")
    paragraph = _improve_text(input_string)
    return paragraph

def _improve_text(info):
    prompts = [
        SystemMessage(content = FUNCTION_CONFIG["system_prompt"]),
        HumanMessage(content = info)
    ]
    completion = _invoke_llm(prompts)
    logger.debug(f"COMPLETION:\n{completion}")
    return completion

def _invoke_llm(messages):
    chat = ChatModel.create(FUNCTION_CONFIG["llm"])
    result = chat.invoke(messages)
    return result.content


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    It either prints the manifest or launches the web application
    based on the input parameter `local` : 
    - If True, the tool's manifest is printed.
    - If False, the web application is launched.
    """
    if local:
        return basic_copywriter.get_manifest()
    basic_copywriter.run_app()
    return None


if __name__ == "__main__":
     # Run in web application mode.
    main(False)
