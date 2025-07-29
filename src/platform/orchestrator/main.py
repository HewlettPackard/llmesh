#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Endpoint Server with Reasoning Engine Integration

This script replaces the Flask web app with a FastAPI-based OpenAI-compatible
LLM endpoint, while keeping project handling and reasoning engine integration.
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from athon.system import Config, Logger, ToolDiscovery, ChatEndpoint
from athon.chat import ChatMemory
from athon.agents import ToolRepository, ReasoningEngine
from src.platform.mcp.main import platform_registry


# Load configuration
PATH = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(PATH, 'config.yaml')
CONFIG = Config(config_path).get_settings()
logger = Logger().configure(CONFIG['logger']).get_logger()

# Global project context
project_settings = {
    "tool_repository": None,
    "projects": [],
    "engine": None
}

async def main():
    """
    Main function that starts the FastAPI app using Uvicorn.
    Reads host, port, and optional SSL context from the configuration.
    """
    logger.info("Starting the LLM Endpoint...")
    webapp_config = CONFIG.get('webapp') or {'ip': '127.0.0.1'}
    app_run_args = {
        'host': webapp_config.get('ip', '127.0.0.1'),
        'port': webapp_config.get('port', 5001)
    }
    if 'ssh_cert' in webapp_config:
        cert_config = webapp_config['ssh_cert']
        app_run_args['ssl_certfile'] = cert_config.get('certfile')
        app_run_args['ssl_keyfile'] = cert_config.get('keyfile')
    app = await _create_llm_app(CONFIG)
    uvicorn.run(app, **app_run_args)

async def _create_llm_app(config):
    """
    Create the FastAPI application and configure its routes.
    """
    logger.debug("Creating FastAPI LLM App")
    await _init_project(config)
    llm_endpoint_config = _prepare_llm_endpoint_config(config)
    chat_endpoint = ChatEndpoint(llm_endpoint_config)
    app = FastAPI()
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        """
        OpenAI-compatible endpoint for chat completions. Uses the reasoning engine
        to generate a response based on the latest user message.
        """
        try:
            body = await request.json()
            chat_request = ChatEndpoint.ChatRequest(**body)
            chat_endpoint.validate_request(chat_request)
            matched_project = _match_project(chat_request.model)
            engine = project_settings["engine"]
            _configure_engine(engine, matched_project)
            engine_input = _prepare_engine_input(engine, chat_request.messages)
            result = engine.run(engine_input)
            if result.status == "failure":
                raise RuntimeError(result.error_message)
            if chat_request.stream:
                return _build_streaming_response(chat_endpoint, result.completion)
            return chat_endpoint.build_response(chat_request, content=result.completion)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error handling chat completion: %s", exc)
            return JSONResponse(status_code=500, content={"error": str(exc)})

    @app.get("/v1/models")
    async def get_models():
        """
        OpenAI-compatible endpoint to list available models.
        """
        return chat_endpoint.get_models()

    return app

async def _init_project(config):
    project_settings["tool_repository"] = await _discover_project_tools(
        config["projects"],
        config["chat"]["tools"],
        config["chat"]["discovery"])
    project_settings["projects"] = _create_project_manager(
        config["projects"],
        project_settings["tool_repository"])
    project_settings["engine"] = ReasoningEngine.create(config["chat"])

async def _discover_project_tools(projects_config, tools_config, discovery_config, update=False):
    tool_repository = ToolRepository.create(tools_config)
    tool_discovery = ToolDiscovery(discovery_config)
    tool_id_counter = 1

    # First, discover tools from platform registry if available
    if platform_registry and hasattr(platform_registry, 'registry') and platform_registry.registry:
        logger.info("Discovering tools from platform registry")
        try:
            # Get all registered platform tools
            registry_tools = await _get_platform_tools()
            for tool_name, tool_info in registry_tools.items():
                # Find which projects should have this tool
                for project in projects_config:
                    # Check if tool is listed for this project (by name or URL pattern)
                    for tool_ref in project["tools"]:
                        # Handle mcp:// prefixed references
                        if tool_ref.startswith("mcp://"):
                            mcp_tool_name = tool_ref.replace("mcp://", "")
                            if tool_name == mcp_tool_name:
                                tool_metadata = {
                                    "id": tool_id_counter,
                                    "project": project["name"],
                                    "name": tool_info["name"],
                                    "interface": tool_info.get("interface", {}).get("fields")
                                }
                                if update:
                                    tool_repository.update_tool(tool_info["name"], tool_info["tool"], tool_metadata)
                                else:
                                    tool_repository.add_tool(tool_info["tool"], tool_metadata)
                                tool_id_counter += 1
                                logger.info(f"Added tool {tool_info['name']} from platform registry to project {project['name']}")
                                break
        except Exception as e:
            logger.warning(f"Failed to discover tools from platform registry: {e}")

    # Then discover tools from URLs (backward compatibility)
    for project in projects_config:
        for tool in project["tools"]:
            # Skip if it's an MCP reference (already handled above)
            if tool.startswith("mcp://"):
                continue
            # Skip if already discovered
            result = tool_repository.get_tools()
            if result.status == "success" and tool in [t["metadata"]["name"] for t in result.tools]:
                continue
            tool_info = tool_discovery.discover_tool(tool)
            if tool_info:
                tool_metadata = {
                    "id": tool_id_counter,
                    "project": project["name"],
                    "name": tool_info["name"],
                    "interface": tool_info.get("interface", {}).get("fields")
                }
                if update:
                    tool_repository.update_tool(tool_info["name"], tool_info["tool"], tool_metadata)
                else:
                    tool_repository.add_tool(tool_info["tool"], tool_metadata)
                tool_id_counter += 1
    return tool_repository


async def _get_platform_tools():
    """Get all tools from the platform registry."""
    tools = {}
    if platform_registry.registry:
        for name, server_info in platform_registry.registry.servers.items():
            if hasattr(server_info, 'server') and hasattr(server_info.server, 'tools'):
                for tool_name, tool_func in server_info.server.tools.items():
                    tools[tool_name] = {
                        "name": tool_name,
                        "tool": tool_func,
                        "port": server_info.config.get("port"),
                        "interface": {}
                    }
    return tools

def _create_project_manager(projects_config, tool_repository):
    project_manager = []
    project_id_counter = 1
    for project in projects_config:
        project_data = {
            "id": project_id_counter,
            "project": project["name"],
            "tools": _get_tools_names(tool_repository, project["name"]),
            "memory": _get_project_memory(project["memory"])
        }
        project_manager.append(project_data)
        project_id_counter += 1
    return project_manager

def _get_tools_names(tool_repository, project_name):
    result = tool_repository.get_tools(metadata_filter={"project": project_name})
    if result.status == "success":
        return [tool["metadata"]["name"] for tool in result.tools]
    return []

def _get_project_memory(memory_config):
    chat_memory = ChatMemory.create(memory_config)
    result = chat_memory.get_memory()
    if result.status == "success":
        return result.memory
    return None

def _prepare_llm_endpoint_config(config: dict) -> dict:
    project_names = [project.get("name") for project in config.get("projects", [])]
    llm_endpoint = config.get("webapp", {}).get("llm_endpoint", {}).copy()
    llm_endpoint["available_models"] = project_names
    return llm_endpoint

def _match_project(model_name: str) -> dict:
    matched = next(
        (p for p in project_settings["projects"] if p.get("project") == model_name),
        None
    )
    if not matched:
        raise HTTPException(
            status_code=404,
            detail=f"No project found for model '{model_name}'"
        )
    return matched

def _configure_engine(engine, project: dict) -> None:
    engine.set_tools(project["tools"])
    if not getattr(engine.config, "stateless", False):
        engine.set_memory(project["memory"])

def _prepare_engine_input(engine, messages: list) -> str | list:
    if getattr(engine.config, "stateless", False):
        return messages
    return next((m.content for m in reversed(messages) if m.role == "user"), "")

def _build_streaming_response(chat_endpoint, content: str) -> StreamingResponse:
    def event_stream():
        chunk = chat_endpoint.build_stream_chunk(content)
        yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    main()
