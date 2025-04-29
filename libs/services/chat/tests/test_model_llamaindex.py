#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ChatModel factory and LLamaIndex model flavors. The tests 
ensure that the factory method correctly initializes and returns instances of the appropriate
model types based on the given configuration. It also tests the specific behavior of each 
model's methods to ensure correct setup and functionality.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from llama_index.llms.openai import OpenAI
from libs.services.chat.model import ChatModel
from libs.services.chat.models.llamaindex.openai import (
    LlamaIndexOpenAIModel)


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


@patch.object(OpenAI, 'complete')
def test_llamaindex_openaimodel_invoke(mock_complete, llamaindex_openai_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LlamaIndexOpenAIModel to verify it returns a result
    with the correct status, content, and metadata.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.text = "Mocked response"
    mock_response.additional_kwargs = {"key": "value"}
    # Set the mock to return the mock response object
    mock_complete.return_value = mock_response
    llm = LlamaIndexOpenAIModel(llamaindex_openai_model_config)
    result = llm.invoke("Hello, world!")
    assert result.status == "success"
    assert result.content == "Mocked response"
    assert result.metadata == {"key": "value"}  # Update this to match expected metadata
    mock_complete.assert_called_once_with("Hello, world!")


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
