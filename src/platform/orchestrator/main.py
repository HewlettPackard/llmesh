#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Endpoint Server with Reasoning Engine Integration

This script replaces the Flask web app with a FastAPI-based OpenAI-compatible
LLM endpoint, while keeping project handling and reasoning engine integration.
"""

import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from athon.system import Config, Logger, ToolDiscovery, ChatEndpoint
from athon.chat import ChatMemory
from athon.agents import ToolRepository, ReasoningEngine


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

def main():
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
    app = _create_llm_app(CONFIG)
    uvicorn.run(app, **app_run_args)

def _create_llm_app(config):
    """
    Create the FastAPI application and configure its routes.
    """
    logger.debug("Creating FastAPI LLM App")
    _init_project(config)
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
            # Match project by name against requested model
            matched_project = next(
                (project for project in project_settings["projects"]
                if project.get("project") == chat_request.model),
                None
            )
            if not matched_project:
                raise HTTPException(
                    status_code=404,
                    detail=f"No project found for model '{chat_request.model}'"
                )
            # Set tools and memory for the matched project
            project_settings["engine"].set_tools(matched_project["tools"])
            project_settings["engine"].set_memory(matched_project["memory"])
            user_message = next(
                (m.content for m in reversed(chat_request.messages)
                if m.role == "user"), ""
            )
            result = project_settings["engine"].run(user_message)
            if result.status == "failure":
                raise RuntimeError(result.error_message)
            if chat_request.stream:
                def event_stream():
                    # You can later tokenize here if needed
                    chunk = chat_endpoint.build_stream_chunk(result.completion)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                return StreamingResponse(event_stream(), media_type="text/event-stream")
            return chat_endpoint.build_response(chat_request, content=result.completion)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error handling chat completion: %s", exc)
            return JSONResponse(
                status_code=500,
                content={"error": str(exc)}
            )

    @app.get("/v1/models")
    async def get_models():
        """
        OpenAI-compatible endpoint to list available models.
        """
        return chat_endpoint.get_models()

    return app

def _init_project(config):
    project_settings["tool_repository"] = _discover_project_tools(
        config["projects"],
        config["chat"]["tools"],
        config["chat"]["discovery"])
    project_settings["projects"] = _create_project_manager(
        config["projects"],
        project_settings["tool_repository"])
    project_settings["engine"] = ReasoningEngine.create(config["chat"])

def _discover_project_tools(projects_config, tools_config, discovery_config, update=False):
    tool_repository = ToolRepository.create(tools_config)
    tool_discovery = ToolDiscovery(discovery_config)
    tool_id_counter = 1
    for project in projects_config:
        for tool in project["tools"]:
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


if __name__ == "__main__":
    main()
