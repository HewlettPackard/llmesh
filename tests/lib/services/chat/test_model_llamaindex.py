#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ChatModel factory and LLamaIndex model flavors. The tests 
ensure that the factory method correctly initializes and returns instances of the appropriate
model types based on the given configuration. It also tests the specific behavior of each 
model's methods to ensure correct setup and functionality.
"""

import os
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage, MessageRole
from src.lib.services.chat.model import ChatModel
from src.lib.services.chat.models.llamaindex.openai import (
    LlamaIndexOpenAIModel
)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "LlamaIndexOpenAI",
            "model_name": "gpt-3",
            "api_key": "your_api_key",
            "system_prompt": "your_prompt"
        },
        LlamaIndexOpenAIModel
    ),
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    model_instance = ChatModel.create(config)
    assert isinstance(model_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        ChatModel.create({"type": "UnknownType", "model_name": "invalid"})


@pytest.fixture
def llamaindex_openai_model_config():
    """
    Mockup LLamaIndex_OpenAI model
    """
    return {
        "type": "LlamaIndexOpenAI",
        "model_name": "gpt-3",
        "api_key": "your_api_key"
    }


@patch.object(OpenAI, 'chat')
@pytest.mark.parametrize("input_data,expected_content", [
    (
        "Hello",
        "Mocked response for string"
    ),
    (
        ChatMessage(role=MessageRole.USER, content="Hi"),
        "Mocked response for single ChatMessage"
    ),
    (
        ["Hey", "What's up?"],
        "Mocked response for list of strings"
    ),
    (
        [ChatMessage(role=MessageRole.USER, content="Hi again")],
        "Mocked response for list of ChatMessages"
    ),
])
def test_llamaindex_openaimodel_invoke_variants(
    mock_chat, llamaindex_openai_model_config, input_data, expected_content):  # pylint: disable=W0621
    """
    Test the invoke method of LlamaIndexOpenAIModel to verify it returns a result
    with the correct status, content, and metadata.
    """
    mock_response = MagicMock()
    mock_response.text = expected_content
    mock_response.additional_kwargs = {"source": "unit_test"}
    mock_chat.return_value = mock_response
    llm = LlamaIndexOpenAIModel(llamaindex_openai_model_config)
    result = llm.invoke(input_data)
    assert result.status == "success"
    assert result.content == expected_content
    assert result.metadata == {"source": "unit_test"}
    mock_chat.assert_called_once()


@patch.object(OpenAI, 'stream_chat')
def test_llamaindex_openaimodel_stream(mock_stream_chat, llamaindex_openai_model_config):  # pylint: disable=W0621
    """
    Test the stream method of LlamaIndexOpenAIModel to ensure it yields tokens.
    """
    mock_chunk = MagicMock()
    mock_chunk.delta = "token"
    mock_stream_chat.return_value = iter([mock_chunk, mock_chunk])
    llm = LlamaIndexOpenAIModel(llamaindex_openai_model_config)
    tokens = list(llm.stream("hello"))
    assert tokens == ["token", "token"]
    mock_stream_chat.assert_called_once()


@patch.object(OpenAI, 'achat', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_llamaindex_openaimodel_ainvoke(mock_achat, llamaindex_openai_model_config):  # pylint: disable=W0621
    """
    Test the ainvoke method of LlamaIndexOpenAIModel to verify it works with async call.
    """
    mock_response = MagicMock()
    mock_response.text = "Async response"
    mock_response.additional_kwargs = {"mode": "async"}
    mock_achat.return_value = mock_response
    llm = LlamaIndexOpenAIModel(llamaindex_openai_model_config)
    result = await llm.ainvoke("Hi async")
    assert result.status == "success"
    assert result.content == "Async response"
    assert result.metadata == {"mode": "async"}
    mock_achat.assert_awaited_once()


@patch.object(OpenAI, 'astream_chat')
@pytest.mark.asyncio
async def test_llamaindex_openaimodel_astream(mock_astream_chat, llamaindex_openai_model_config):  # pylint: disable=W0621
    """
    Test the astream method of LlamaIndexOpenAIModel to ensure it yields async tokens.
    """
    mock_chunk = MagicMock()
    mock_chunk.delta = "async_token"
    # ✅ Define async generator and return its result
    async def async_gen():
        yield mock_chunk
        yield mock_chunk
    mock_astream_chat.return_value = async_gen()  # <== IMPORTANT!
    model = LlamaIndexOpenAIModel(llamaindex_openai_model_config)
    result = []
    async for token in model.astream("Hi"):
        result.append(token)
    assert result == ["async_token", "async_token"]
    mock_astream_chat.assert_called_once()


def test_llamaindex_openaimodel_get_model(llamaindex_openai_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LlamaIndexOpenAIModel to verify it returns the model instance.
    """
    factory = ChatModel.create(llamaindex_openai_model_config)
    result = factory.get_model()
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, OpenAI)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
