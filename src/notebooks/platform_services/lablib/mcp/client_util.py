#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Common lab utilities for MCP clients.

This module provides shared functionality for MCP client examples,
including interaction with a Language Model (LLM) for tasks like
translation, and a common demonstration sequence (`run_demo`)
to showcase client-server interactions. It handles LLM setup,
response printing, and orchestrates calls to list and use
MCP tools, resources, and prompts.
"""

import json
import pprint
from typing import Any
from langchain.schema import SystemMessage, HumanMessage
from mcp import ClientSession
from self_serve_platform.chat.models.langchain_chat_openai import LangChainChatOpenAIModel
from src.notebooks.platform_services.lablib.env_util import get_services_env

# LLM Setup
llm_api_key, llm_model_name, _ = get_services_env()
LLM_CONFIG = {
    'type': 'LangChainChatOpenAI',
    'api_key': llm_api_key,
    'model_name': llm_model_name,
    'temperature': 0.7,
}
chat = LangChainChatOpenAIModel(config=LLM_CONFIG)

def print_response(name: str, response: Any) -> None:
    """Prints a formatted response object."""
    print(f"\n===== {name} =====")
    if hasattr(response, "model_dump"):
        pprint.pprint(response.model_dump())
    elif hasattr(response, "dict"):
        pprint.pprint(response.dict())
    else:
        pprint.pprint(response)
    print(f"===== End of {name} =====")

async def pirate_translate(text: str, context: str) -> str:
    """Uses LLM to translate text to pirate speech using MCP context."""
    messages = [
        SystemMessage(content=f"Use this context: {context}"),
        HumanMessage(content=f"Translate to pirate: {text}")
    ]
    result = chat.invoke(messages)
    return result.content if result.status == "success" else text

async def run_demo(session: ClientSession):
    """Runs the common sequence of operations for an MCP client session."""
    print("===== Initialize Client and Make Session Calls =====")
    await session.initialize()
    
    # Get MCP resources
    tools = await session.list_tools()
    resources = await session.list_resources()
    prompts = await session.list_prompts()
    
    # Get core components
    add_result = await session.call_tool("add", {"a": 5, "b": 3.5})
    greeting = await session.read_resource("greeting://World")
    prompt_params = {"user_query": "What's the weather?"}
    # Ensure 'mode' is provided if the prompt expects it, default to 'translate' if not specified.
    # The common prompt definition has 'translate' as default, so this should be fine.
    prompt = await session.get_prompt("system_prompt", prompt_params)

    # Generate pirate translations using MCP data
    pirate_math = await pirate_translate(
        f"The sum be {add_result.content[0].text}", 
        "Explain numeric results in pirate speech"
    )
    
    pirate_greeting = await pirate_translate(
        json.loads(greeting.contents[0].text)["text"],
        "Convert greetings to pirate talk"
    )
    
    weather_query = ""
    if prompt.messages and len(prompt.messages) > 0:
        # Assuming the last message is the user query part we want to translate
        last_message_content = prompt.messages[-1].content
        if hasattr(last_message_content, 'text'): # For TextContent
            weather_query = last_message_content.text
        elif isinstance(last_message_content, str): # For plain string
            weather_query = last_message_content


    pirate_weather_context_messages = []
    for msg in prompt.messages:
        if hasattr(msg.content, 'text'):
            pirate_weather_context_messages.append(msg.content.text)
        elif isinstance(msg.content, str):
             pirate_weather_context_messages.append(msg.content)
    
    pirate_weather = await pirate_translate(
        weather_query,
        "\n".join(pirate_weather_context_messages)
    )

    # Print enhanced results
    print("===== Printing Session Calls Details =====")
    print(f"Tools: {[t.name for t in tools.tools]}")
    print(f"Resources: {[r.uri for r in resources.resources]}")
    print(f"Prompts: {[p.name for p in prompts.prompts]}")
    
    print_response("Addition Result", {
        **add_result.model_dump(),
        "pirate_translation": pirate_math
    })
    
    print_response("Greeting", {
        **greeting.model_dump(),
        "pirate_version": pirate_greeting
    })
    
    print_response("System Prompt", {
        **prompt.model_dump(),
        "current_query_pirate": pirate_weather
    })

    # Print direct accessors with translations
    print("===== Printing Direct Value Accessors =====")
    print(f"Numeric addition result: {add_result.content[0].text}")
    print(f"Pirate math: {pirate_math}")
    print(f"Original greeting: {json.loads(greeting.contents[0].text)['text']}")
    print(f"Pirate greeting: {pirate_greeting}")
    print(f"Last message original: {weather_query}")
    print(f"Last message pirate: {pirate_weather}")
    
    print("\n===== Demo Complete =====")
