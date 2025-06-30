#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module initializes an agentic tool of the platform chat service.
It uses MCP for tool registration and exposure.
"""

import os
import asyncio
import traceback
from athon.chat import (
    ChatModel,
    ChatMemory,
    MessageManager,
    PromptRender,
    MessageRole
)
from athon.system import (
    Config,
    Logger
)
from src.platform.mcp.main import platform_registry

# Load configuration
PATH = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(PATH, 'config.yaml')
config = Config(config_path).get_settings()
# Config settings
SERVICE_CONFIG = config["service"]
PROMPT_CONFIG = config["prompts"]
LOG_CONFIG = config['logger']

# Create global objects
logger = Logger().configure(LOG_CONFIG).get_logger()
memory = ChatMemory.create(SERVICE_CONFIG["memory"])
message_manager = MessageManager.create(SERVICE_CONFIG["message_manager"])


async def chat(query: str, new: bool=False, personas: str="assistant") -> str:
    """
    Answer chat discussion
    """
    try:
        logger.info("Chat Service execution")
        messages = _get_messages(query, new, personas)
        completion = _generate_completion(messages)
        _store_in_memory(messages, completion)
        return completion
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Unhandled exception in chat tool: {e}")
        logger.debug(traceback.format_exc())
        return "An error occurred while processing your request."

def _get_messages(query, new, personas):
    try:
        messages = []
        messages = _concatenate_messages(messages, _get_system_message(personas))
        messages = _concatenate_messages(messages, _get_memory_messages(new))
        messages = _concatenate_messages(messages, _get_user_message(query))
        return messages
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Failed to build message list: {e}")
        raise

def _concatenate_messages(messages, new_messages):
    result = message_manager.add_messages(messages, new_messages)
    if result.status == "success":
        return result.messages
    logger.error("Failed to concatenate the messages")
    return []

def _get_system_message(personas):
    try:
        prompt = PromptRender.create(PROMPT_CONFIG)
        persona_dict = {}
        for item in SERVICE_CONFIG.get("personas", []):
            if isinstance(item, dict):
                persona_dict.update(item)
        if personas and personas in persona_dict:
            result = prompt.load(persona_dict[personas])
            if result.status == "success":
                system_prompt = result.content
            else:
                logger.warning(f"Failed to load persona prompt: {personas}")
                system_prompt = SERVICE_CONFIG["system_prompt"]
        else:
            system_prompt = SERVICE_CONFIG["system_prompt"]
        result = message_manager.create_message(MessageRole.SYSTEM, system_prompt)
        if not result.status == "success" or not result.messages:
            raise ValueError("Failed to create system message")
        return result.messages
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Failed to load system prompt, using default. Error: {e}")
        return message_manager.create_message(MessageRole.SYSTEM, SERVICE_CONFIG["system_prompt"])

def _get_memory_messages(new):
    try:
        memory_messages = []
        if memory:
            if new:
                memory.clear()
            else:
                result = memory.get_messages()
                if not result.status == "success" or not result.messages:
                    raise ValueError("Failed to get memory messages")
                memory_messages = result.messages
        messages = message_manager.from_framework_messages(memory_messages)
        return messages
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error accessing memory messages: {e}")
        return []

def _get_user_message(query):
    try:
        result = message_manager.create_message(MessageRole.USER, query)
        if not result.status == "success" or not result.messages:
            raise ValueError("Failed to create system message")
        return result.messages
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Failed to create user message: {e}")
        raise

def _generate_completion(messages):
    try:
        prompts = message_manager.to_framework_messages(messages)
        chat_model = ChatModel.create(SERVICE_CONFIG["llm"])
        result = chat_model.invoke(prompts)
        if not result.status == "success":
            raise ValueError("Failed to create system message")
        logger.debug(f"COMPLETION:\n{result.content}")
        return result.content
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Failed to generate completion: {e}")
        logger.debug(traceback.format_exc())
        raise

def _store_in_memory(messages, completion):
    try:
        if not memory:
            return
        result = message_manager.create_message(MessageRole.ASSISTANT, completion)
        if not result.status == "success":
            raise ValueError("Failed to create system message")
        messages_to_save = message_manager.to_framework_messages([
            messages[-1],
            result.messages[0]
        ])
        for message in messages_to_save:
            result = memory.save_message(message)
            if not result.status == "success":
                raise ValueError("Failed to create system message")
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Failed to store messages in memory: {e}")


async def register():
    """
    Register this tool with the platform registry.
    """
    try:
        # Get tool description from prompt
        prompt = PromptRender.create(PROMPT_CONFIG)
        result = prompt.load("tool_description")
        description = result.content if hasattr(result, 'content') else config["tool"]["description"]

        # Register with platform - pass webapp config directly
        server = await platform_registry.register_platform_tool(
            name="chat",
            func=chat,
            config=config["webapp"],
            description=description
        )
        logger.info("Chat service registered successfully")
        return server

    except Exception as e:
        logger.error(f"Failed to register chat service: {e}")
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
        "name": "chat",
        "function": "chat",
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
            logger.info(f"Chat server running on {config['webapp']['ip']}:{config['webapp']['port']}")
            await asyncio.Event().wait()

    asyncio.run(run_server())
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)
