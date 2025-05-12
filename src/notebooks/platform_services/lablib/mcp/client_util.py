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
from typing import Any, List
from langchain.schema import SystemMessage, HumanMessage
from mcp import ClientSession
from src.lib.services.chat.models.langchain.chat_openai import LangChainChatOpenAIModel
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

def print_step(step_name: str, description: str = "") -> None:
    """Prints a clear step header with optional description."""
    print(f"\n{'='*20} STEP: {step_name} {'='*20}")
    if description:
        print(f"Description: {description}")
    print()

def print_response(name: str, response: Any, extra_info: dict = None) -> None:
    """Prints a formatted response object with optional extra information."""
    print(f"\n--- {name} Response ---")
    if hasattr(response, "model_dump"):
        pprint.pprint(response.model_dump())
    elif hasattr(response, "dict"):
        pprint.pprint(response.dict())
    else:
        pprint.pprint(response)
    
    if extra_info:
        print("\n--- Additional Information ---")
        pprint.pprint(extra_info)
    print(f"--- End of {name} ---")

async def demonstrate_tool_usage(session: ClientSession, tools: List[Any]):
    """Demonstrates various tool calls with explanations."""
    print_step("Tool Usage", "Calling different MCP tools to show functionality")
    
    # Demonstrate each available tool
    for tool in tools:
        print(f"\n🔧 Using tool: {tool.name}")
        print(f"   Description: {getattr(tool, 'description', 'No description')}")
        
        if tool.name == "add":
            result = await session.call_tool("add", {"a": 5, "b": 3.5})
            print_response("Add Tool", result, {
                "operation": "5 + 3.5",
                "explanation": "Basic addition using MCP tool"
            })
            
        elif tool.name == "add_two":
            result = await session.call_tool("add_two", {"a": 10, "b": 7})
            print_response("Add Two Tool", result, {
                "operation": "10 + 7",
                "explanation": "Another addition tool variant"
            })
            
        elif tool.name == "get_weather":
            # Try calling weather tool with a location
            try:
                result = await session.call_tool("get_weather", {"location": "San Francisco"})
                print_response("Weather Tool", result, {
                    "location": "San Francisco",
                    "explanation": "Getting weather information"
                })
            except Exception as e:
                print(f"   Could not call weather tool: {e}")

async def demonstrate_resource_access(session: ClientSession, resources: List[Any]):
    """Demonstrates accessing different MCP resources."""
    print_step("Resource Access", "Reading data from MCP resources")
    
    for resource in resources:
        print(f"\n📄 Accessing resource: {resource.uri}")
        print(f"   Name: {getattr(resource, 'name', 'Unknown')}")
        print(f"   Description: {getattr(resource, 'description', 'No description')}")
        
        try:
            if str(resource.uri).startswith("greeting://"):
                result = await session.read_resource(resource.uri)
                content = json.loads(result.contents[0].text)
                print_response("Greeting Resource", result, {
                    "parsed_content": content,
                    "explanation": "Template-based greeting resource"
                })
            elif str(resource.uri).startswith("config://"):
                result = await session.read_resource(resource.uri)
                print_response("Config Resource", result, {
                    "explanation": "Configuration data resource"
                })
        except Exception as e:
            print(f"   Error reading resource: {e}")

async def demonstrate_prompt_usage(session: ClientSession, prompts: List[Any]):
    """Demonstrates using MCP prompts."""
    print_step("Prompt Usage", "Getting and using MCP prompts")
    
    for prompt in prompts:
        print(f"\n💬 Using prompt: {prompt.name}")
        print(f"   Description: {getattr(prompt, 'description', 'No description')}")
        
        if prompt.name == "system_prompt":
            # Try different modes if supported
            modes = ["translate", "explain", "help"]
            for mode in modes:
                print(f"\n   Trying mode: {mode}")
                try:
                    prompt_params = {
                        "user_query": "What's the weather like today?",
                        "mode": mode
                    }
                    result = await session.get_prompt("system_prompt", prompt_params)
                    print_response(f"System Prompt (mode={mode})", result, {
                        "parameters": prompt_params,
                        "message_count": len(result.messages),
                        "explanation": f"Prompt in {mode} mode"
                    })
                    break  # Just show one successful mode
                except Exception as e:
                    print(f"   Mode {mode} failed: {e}")

async def pirate_translate(text: str, context: str) -> str:
    """Uses LLM to translate text to pirate speech using MCP context."""
    messages = [
        SystemMessage(content=f"Use this context: {context}"),
        HumanMessage(content=f"Translate to pirate: {text}")
    ]
    result = chat.invoke(messages)
    return result.content if result.status == "success" else text

async def run_demo(session: ClientSession):
    """Runs the comprehensive MCP demonstration."""
    print("="*50)
    print("MCP Client-Server Demonstration")
    print("="*50)
    
    # Initialize the session
    print_step("Initialization", "Establishing connection with MCP server")
    await session.initialize()
    print("✅ Successfully connected to MCP server")
    
    # Discover available capabilities
    print_step("Discovery", "Finding what the server offers")
    tools = await session.list_tools()
    resources = await session.list_resources()
    prompts = await session.list_prompts()
    
    print(f"🔧 Found {len(tools.tools)} tools: {[t.name for t in tools.tools]}")
    print(f"📄 Found {len(resources.resources)} resources: {[r.uri for r in resources.resources]}")
    print(f"💬 Found {len(prompts.prompts)} prompts: {[p.name for p in prompts.prompts]}")
    
    # Demonstrate each MCP primitive
    await demonstrate_tool_usage(session, tools.tools)
    await demonstrate_resource_access(session, resources.resources)
    await demonstrate_prompt_usage(session, prompts.prompts)
    
    # Show integration example with LLM
    print_step("LLM Integration", "Using MCP data with Language Model")
    
    # Get some data from MCP
    add_result = await session.call_tool("add", {"a": 42, "b": 8})
    
    # Convert to pirate language (fun demonstration of LLM integration)
    pirate_math = await pirate_translate(
        f"The result is {add_result.content[0].text}",
        "Explain mathematical results in a fun, pirate-style way"
    )
    
    print_response("LLM Integration Example", {
        "mcp_result": add_result.model_dump(),
        "llm_enhancement": pirate_math,
        "explanation": "Shows how MCP data can be enhanced with LLM processing"
    })
    
    print("\n" + "="*50)
    print("✅ MCP Demo Complete!")
    print("="*50)