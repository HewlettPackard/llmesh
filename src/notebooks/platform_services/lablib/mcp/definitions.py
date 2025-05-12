#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Defines common lab components for MCP server instances.

This module includes functions to register standard tools (e.g., arithmetic,
simulated external API calls), resources (e.g., dynamic greetings, static
configuration), and prompts (e.g., templated system messages for LLMs)
with a FastMCP server. These definitions can be reused across different
MCP server examples.
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import UserMessage, AssistantMessage
from mcp.types import TextContent
import json
from typing import List, Union

def register_tools(mcp: FastMCP):
    """Registers common tools to the MCP instance."""
    @mcp.tool()
    async def add(a: float, b: float) -> float:
        """Add two numbers"""
        return a + b

    @mcp.tool()
    async def get_weather(city: str) -> dict:
        """Get current weather for a city"""
        # Simulated API call
        return {"city": city, "temp": 22.5, "conditions": "sunny"}

def register_resources(mcp: FastMCP):
    """Registers common resources to the MCP instance."""
    @mcp.resource("greeting://{name}")
    async def greeting_resource(name: str) -> TextContent:
        """Dynamic greeting resource"""
        return TextContent(type="text", text=f"Hello, {name}!")

    @mcp.resource("config://settings")
    async def config_resource() -> TextContent:
        """Server configuration"""
        return TextContent(type="text", text=json.dumps({"version": "1.0", "status": "active"}))

def register_prompts(mcp: FastMCP):
    """Registers common prompts to the MCP instance."""
    @mcp.prompt("system_prompt")
    async def system_prompt_template(user_query: str, mode: str = 'translate') -> List[Union[str, UserMessage, AssistantMessage]]:
        """System prompt template for chat responses for one of two modes.
        
        Mode 1: Translate user query to pirate language.
        Mode 2: Answer the user query in pirate language.

        Args:
            user_query (str): The user's query.
            mode (str): The mode of operation. Can be 'translate' or 'answer'.

        Returns:
            A list containing system instruction string and message objects.
        """
        if mode not in ('translate', 'answer'):
            raise ValueError("Mode must be 'translate' or 'answer'.")
        
        system_instruction = f"You are a helpful assistant who is fluent in pirate language. Please '{mode}' the following text."
        
        examples = []
        if mode == 'translate':
            examples = [
                UserMessage(content="Hello, how are you today?"),
                AssistantMessage(content="Ahoy there, how be ye this fine day, matey?"),
                UserMessage(content="I need to find a restaurant nearby."),
                AssistantMessage(content="Arr, I be needin' to find a place to fill me belly nearby, savvy?"),
            ]
        else:  # answer mode
            examples = [
                UserMessage(content="What is the capital of Spain?"),
                AssistantMessage(content="Arr, the capital o' Spain be Madrid, me hearty! A fine port city full o' treasure and grog, it be!"),
                UserMessage(content="How do I bake a chocolate cake?"),
                AssistantMessage(content="Ahoy! To bake a chocolate cake, ye need to gather yer ingredients: flour, sugar, cocoa powder, and other treasures. Mix 'em together in a big bowl, pour into a vessel, and cook in yer hot box until a knife comes out clean, arr! Don't be burnin' it or the crew will make ye walk the plank!"),
            ]
        
        examples.append(UserMessage(content=user_query))
        return [system_instruction] + examples
