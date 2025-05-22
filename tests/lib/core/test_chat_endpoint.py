#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the functionality of the ChatEndpoint class from 
the chat_completion_engine module.
It includes tests for request validation, response generation, and 
handling of unexpected fields.
"""

import os
import logging
import pytest
from src.lib.core.chat_endpoint import ChatEndpoint


@pytest.fixture
def chat_endpoint():
    """
    Fixture to create a ChatEndpoint instance with default config.
    
    Returns:
        ChatEndpoint: An instance of ChatEndpoint.
    """
    return ChatEndpoint(config={"available_models": ["gpt-3.5-turbo", "local-model"]})


@pytest.fixture
def basic_request():
    """
    Fixture to provide a minimal valid chat request.

    Returns:
        ChatEndpoint.ChatRequest: A basic request with one user message.
    """
    return ChatEndpoint.ChatRequest(
        model="gpt-3.5-turbo",
        messages=[ChatEndpoint.Message(role="user", content="Hello")]
    )


def test_validate_request_success(chat_endpoint, basic_request):  # pylint: disable=W0621
    """
    Test to verify that a valid request passes validation without errors.
    """
    chat_endpoint.validate_request(basic_request)  # Should not raise


def test_validate_request_missing_model(chat_endpoint):  # pylint: disable=W0621
    """
    Test to verify that validation fails if 'model' is missing.
    """
    with pytest.raises(Exception) as exc_info:
        chat_endpoint.validate_request(
            ChatEndpoint.ChatRequest(messages=[{"role": "user", "content": "Hi"}])
        )
    assert "model" in str(exc_info.value)


def test_validate_request_missing_messages(chat_endpoint):  # pylint: disable=W0621
    """
    Test to verify that validation fails if 'messages' is missing.
    """
    with pytest.raises(Exception) as exc_info:
        chat_endpoint.validate_request(
            ChatEndpoint.ChatRequest(model="gpt-3.5-turbo", messages=[])
        )
    assert "messages" in str(exc_info.value)


def test_build_response_defaults(chat_endpoint, basic_request):  # pylint: disable=W0621
    """
    Test to verify that the default response echoes the user's message.
    """
    response = chat_endpoint.build_response(basic_request)
    assert response.model == basic_request.model
    assert response.choices[0].message.role == "assistant"
    assert "Hello" in response.choices[0].message.content
    assert response.id.startswith("chatcmpl-")
    assert isinstance(response.created, int)


def test_build_response_custom_content(chat_endpoint, basic_request):  # pylint: disable=W0621
    """
    Test to verify that a custom assistant reply is returned when provided.
    """
    custom_reply = "This is a custom response."
    response = chat_endpoint.build_response(basic_request, content=custom_reply)
    assert response.choices[0].message.content == custom_reply


def test_warn_on_extra_fields(caplog):
    """
    Test to ensure unexpected fields in the request are logged as warnings.
    """
    # Patch logger to propagate so pytest caplog can catch it
    logger = logging.getLogger("ATHON")
    logger.setLevel(logging.WARNING)
    logger.propagate = True
    caplog.set_level("WARNING")
    ChatEndpoint.ChatRequest(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        unexpected_field="test"
    )
    # Print captured logs (optional debug)
    for r in caplog.records:
        print(f"LOG: {r.name} - {r.message}")
    assert any("Unexpected field in request: unexpected_field" in r.message for r in caplog.records)


def test_get_models(chat_endpoint):  # pylint: disable=W0621
    """
    Test to verify that get_models returns the expected model list.
    """
    models_response = chat_endpoint.get_models()
    model_ids = [model.id for model in models_response.data]
    assert "gpt-3.5-turbo" in model_ids
    assert "local-model" in model_ids
    assert models_response.object == "list"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, "-vv"])
