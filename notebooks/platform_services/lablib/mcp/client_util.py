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
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from mcp import ClientSession
from src.lib.services.chat.models.langchain.chat_openai import LangChainChatOpenAIModel
from notebooks.platform_services.lablib.env_util import get_services_env

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

def mcp_messages_to_langchain(mcp_messages: List[Any]) -> List[Any]:
    """Convert MCP prompt messages to LangChain message format."""
    langchain_messages = []

    for msg in mcp_messages:
        # Extract the text content
        if hasattr(msg.content, 'text'):
            text = msg.content.text
        elif isinstance(msg.content, str):
            text = msg.content
        else:
            text = str(msg.content)

        # Convert based on role
        if msg.role == 'system':
            langchain_messages.append(SystemMessage(content=text))
        elif msg.role == 'user':
            langchain_messages.append(HumanMessage(content=text))
        elif msg.role == 'assistant':
            langchain_messages.append(AIMessage(content=text))

    return langchain_messages

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

async def demonstrate_prompt_with_llm(session: ClientSession):
    """Demonstrates using MCP prompts directly with an LLM."""
    print_step("MCP Prompt + LLM Integration", "Using MCP prompts directly with Language Model")

    # Get a prompt from MCP
    try:
        prompt_result = await session.get_prompt("system_prompt", {
            "user_query": "I need to book a dinner reservation",
            "mode": "translate"
        })

        print("✅ Retrieved prompt from MCP server")
        print(f"   Prompt has {len(prompt_result.messages)} messages")

        # Convert MCP messages to LangChain format
        langchain_messages = mcp_messages_to_langchain(prompt_result.messages)

        print("\n📤 Sending messages to LLM...")
        print(f"   Converting {len(langchain_messages)} MCP messages to LangChain format")

        # Use the MCP prompt with the LLM
        llm_result = chat.invoke(langchain_messages)

        if llm_result.status == "success":
            print_response("LLM Response Using MCP Prompt", {
                "mcp_prompt": {
                    "name": "system_prompt",
                    "message_count": len(prompt_result.messages),
                    "last_user_message": prompt_result.messages[-1].content.text if prompt_result.messages else "None"
                },
                "llm_response": llm_result.content,
                "explanation": "LLM processed the MCP prompt and generated a pirate translation"
            })
        else:
            print(f"❌ LLM call failed: {llm_result}")

    except Exception as e:
        print(f"❌ Error using prompt with LLM: {e}")

async def demonstrate_mcp_tools_with_llm(session: ClientSession):
    """Demonstrates using MCP tool results with MCP prompts in an LLM."""
    print_step("Tools + Prompts + LLM", "Complete workflow: MCP tools -> MCP prompts -> LLM")

    try:
        # Step 1: Get data from MCP tool
        print("1️⃣ Getting data from MCP tool...")
        add_result = await session.call_tool("add", {"a": 42, "b": 8})
        math_result = add_result.content[0].text
        print(f"   Tool result: {math_result}")

        # Step 2: Get prompt from MCP server
        print("\n2️⃣ Getting translation prompt from MCP server...")
        prompt_result = await session.get_prompt("system_prompt", {
            "user_query": f"The calculation result is {math_result}",
            "mode": "translate"
        })

        # Step 3: Convert to LangChain and send to LLM
        print("\n3️⃣ Using MCP prompt with LLM...")
        langchain_messages = mcp_messages_to_langchain(prompt_result.messages)
        llm_result = chat.invoke(langchain_messages)

        if llm_result.status == "success":
            print_response("Complete MCP Workflow Result", {
                "step_1_tool_result": math_result,
                "step_2_prompt_messages": len(prompt_result.messages),
                "step_3_llm_result": llm_result.content,
                "explanation": "Full workflow: MCP tool -> MCP prompt -> LLM processing"
            })
        else:
            print(f"❌ LLM call failed: {llm_result}")

    except Exception as e:
        print(f"❌ Error in complete workflow: {e}")

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

    # Demonstrate actual LLM integration with MCP prompts
    await demonstrate_prompt_with_llm(session)
    await demonstrate_mcp_tools_with_llm(session)

    print("\n" + "="*50)
    print("✅ MCP Demo Complete!")
    print("="*50)