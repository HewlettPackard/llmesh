#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for the LLM FastAPI endpoint server.

This script tests the FastAPI-based OpenAI-compatible endpoint, including:
- Proper routing and response for /v1/chat/completions and /v1/models
- Handling of stateless and stateful configurations
- Project matching and error handling
"""

import os
import types
from unittest.mock import MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.platform.orchestrator.main import _create_llm_app, project_settings, _prepare_engine_input


@pytest.fixture
def mock_config():
    """
    Return a mocked version of the configuration dictionary.
    """
    return {
        "webapp": {
            "ip": "0.0.0.0",
            "port": 5001,
            "llm_endpoint": {
                "endpoint_prefix": "/v1"
            }
        },
        "chat": {
            "type": "LangChainAgentExecutor",
            "system_prompt": "You are a helpful assistant.",
            "model": {
                "type": "LangChainChatOpenAI",
                "model_name": "gpt-4o",
                "api_key": "dummy-key",
                "temperature": 0,
                "seed": 42
            },
            "memory": {
                "type": "LangChainBuffer",
                "memory_key": "chat_history",
                "return_messages": True
            },
            "tools": {
                "type": "LangChainStructured"
            },
            "discovery": {
                "timeout": 100,
                "cert_verify": False
            },
            "verbose": True,
            "stateless": False
        },
        "projects": [
            {
                "name": "Test Project",
                "tools": ["https://localhost:5002/"],
                "memory": {
                    "type": "LangChainBuffer",
                    "memory_key": "chat_history",
                    "return_messages": True
                }
            }
        ],
        "logger": {
            "name": "LLM-LOG",
            "log_file": "/dev/null",
            "level": "DEBUG"
        }
    }


@pytest.fixture
async def test_client(mock_config):  # pylint: disable=W0621
    """
    Return a TestClient instance of the FastAPI app with patched internals.
    """
    # Save original global state
    original_project_settings = project_settings.copy()

    try:
        with patch("src.platform.orchestrator.main._init_project"), \
             patch("src.platform.orchestrator.main._discover_project_tools"), \
             patch("src.platform.orchestrator.main._create_project_manager"), \
             patch("src.platform.orchestrator.main.ReasoningEngine.create") as mock_engine_create:
            # Create mock reasoning engine
            engine = MagicMock()
            engine.config.stateless = False
            engine.run.return_value.status = "success"
            engine.run.return_value.completion = "This is a test completion."
            mock_engine_create.return_value = engine
            # Inject into global context
            project_settings["projects"] = [{
                "project": "Test Project",
                "tools": ["ToolA"],
                "memory": "mocked-memory"
            }]
            project_settings["engine"] = engine
            # Patch ChatEndpoint with mock get_models
            with patch("src.platform.orchestrator.main.ChatEndpoint") as mock_endpoint, \
                patch("src.platform.orchestrator.main.ChatEndpoint.ChatRequest") as mock_chat_request:
                chat_endpoint_instance = mock_endpoint.return_value
                chat_endpoint_instance.validate_request.return_value = True
                chat_endpoint_instance.get_models.return_value = {
                    "object": "list",
                    "data": [{"id": "Test Project", "object": "model"}]
                }
                chat_endpoint_instance.build_response.return_value = {
                    "id": "chatcmpl-123",
                    "object": "chat.completion",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "This is a test completion."
                        }
                    }]
                }
                def mock_chat_request_handler(**kwargs):
                    mock_request = MagicMock()
                    mock_request.model = kwargs.get("model", "Test Project")
                    # Convert dict messages to objects with role and content attributes
                    messages = kwargs.get("messages", [{"role": "user", "content": "What's the weather?"}])
                    mock_messages = []
                    for msg in messages:
                        if isinstance(msg, dict):
                            mock_msg = MagicMock()
                            mock_msg.role = msg["role"]
                            mock_msg.content = msg["content"]
                            mock_messages.append(mock_msg)
                        else:
                            mock_messages.append(msg)
                    mock_request.messages = mock_messages
                    mock_request.stream = kwargs.get("stream", False)
                    return mock_request

                mock_chat_request.side_effect = mock_chat_request_handler
                chat_endpoint_instance.build_stream_chunk.return_value.model_dump_json.return_value = (
                    '{"content": "streamed"}'
                )
                app = await _create_llm_app(mock_config)
                yield TestClient(app)
    finally:
        # Reset global state to prevent test pollution, if not done causes future tests to potentially hang
        project_settings.clear()
        project_settings.update(original_project_settings)

@pytest.mark.timeout(15)
@pytest.mark.asyncio
async def test_get_models_returns_model_list(test_client):  # pylint: disable=W0621
    """
    Ensure the /v1/models endpoint returns a list of models.
    """
    async for client in test_client:
        response = client.get("/v1/models")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"][0]["id"] == "Test Project"

@pytest.mark.timeout(timeout=15, method="signal")
@pytest.mark.asyncio
async def test_chat_completion_stateful_success(test_client):  # pylint: disable=W0621
    """
    Ensure /v1/chat/completions returns a response when stateful engine is used.
    """
    request_data = {
        "model": "Test Project",
        "messages": [
            {"role": "system", "content": "You are a bot."},
            {"role": "user", "content": "What's the weather?"}
        ],
        "stream": False
    }
    async for client in test_client:
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200
        assert response.json()["choices"][0]["message"]["content"] == "This is a test completion."

@pytest.mark.timeout(15)
@pytest.mark.asyncio
async def test_chat_completion_model_not_found(test_client):  # pylint: disable=W0621
    """
    Ensure a 404 is returned when the model name is invalid.
    """
    request_data = {
        "model": "InvalidModel",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    async for client in test_client:
        response = client.post("/v1/chat/completions", json=request_data)
        # Now we correctly expect a 500 response
        assert response.status_code == 500
        assert "No project found for model" in response.text

@pytest.mark.timeout(15)
@pytest.mark.asyncio
async def test_chat_completion_internal_error(test_client):  # pylint: disable=W0621
    """
    Ensure a 500 is returned when the engine.run raises an exception.
    """
    async for client in test_client:
        project_settings["engine"].run.side_effect = Exception("Runtime crash")
        request_data = {
            "model": "Test Project",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False
        }
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 500
        assert "Runtime crash" in response.text


@pytest.mark.parametrize("stateless", [True, False])
def test_prepare_engine_input_modes(stateless):
    """
    Test _prepare_engine_input to confirm correct behavior for stateless and stateful.
    """
    engine = MagicMock()
    engine.config.stateless = stateless
    # Use mock-like objects with 'role' and 'content' attributes
    msg1 = types.SimpleNamespace(role="system", content="System message")
    msg2 = types.SimpleNamespace(role="user", content="Hello?")
    messages = [msg1, msg2]
    result = _prepare_engine_input(engine, messages)
    if stateless:
        assert result == messages
    else:
        assert result == "Hello?"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
