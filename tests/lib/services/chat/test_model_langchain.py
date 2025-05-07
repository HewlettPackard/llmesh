#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ChatModel factory and LangChain model flavors. The tests 
ensure that the factory method correctly initializes and returns instances of the appropriate
model types based on the given configuration. It also tests the specific behavior of each 
model's methods to ensure correct setup and functionality.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from src.lib.services.chat.model import ChatModel
from src.lib.services.chat.models.langchain.chat_openai import (
    LangChainChatOpenAIModel)
from src.lib.services.chat.models.langchain.azure_chat_openai import (
    LangChainAzureChatOpenAIModel)
from src.lib.services.chat.models.langchain.chat_google_genai import (
    LangChainChatGoogleGenAIModel)
from src.lib.services.chat.models.langchain.chat_anthropic import (
    LangChainChatAnthropicModel)
from src.lib.services.chat.models.langchain.chat_mistralai import (
    LangChainChatMistralAIModel)
from src.lib.services.chat.models.langchain.chat_nvidia import (
    LangChainChatNvidiaModel)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "LangChainChatOpenAI",
            "model_name": "gpt-3",
            "api_key": "your_api_key"
        },
        LangChainChatOpenAIModel
    ),
    (
        {
            "type": "LangChainAzureChatOpenAI",
            "api_key": "your_api_key",
            "azure_deployment": "your_deployment",
            "api_version": "your_version",
            "endpoint": "api_endpoint"
        },
        LangChainAzureChatOpenAIModel
    ),
        (
        {
            "type": "LangChainChatGoogleGenAI",
            "model_name": "gemini-1.5-pro",
            "api_key": "your_api_key"
        },
        LangChainChatGoogleGenAIModel
    ),
    (
        {
            "type": "LangChainChatAnthropic",
            "model_name": "claude-3-5-sonnet-20240620",
            "api_key": "your_api_key"
        },
        LangChainChatAnthropicModel
    ),
    (
        {
            "type": "LangChainChatMistralAI",
            "model_name": "mistral-large-latest",
            "api_key": "your_api_key"
        },
        LangChainChatMistralAIModel
    ),
    (
        {
            "type": "LangChainChatNvidia",
            "model_name": "meta/llama-3.1-8b-instruct",
            "api_key": "your_api_key"
        },
        LangChainChatNvidiaModel
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
def langchain_chatopenai_model_config():
    """
    Mockup LangChain_ChatOpenAI model
    """
    return {
        "type": "LangChainChatOpenAI",
        "model_name": "gpt-3",
        "api_key": "your_api_key"
    }


@patch.object(ChatOpenAI, 'invoke')
def test_langchain_chatopenaimodel_invoke(mock_invoke, langchain_chatopenai_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LangChainChatOpenAIModel to verify it returns a result
    with the correct status, content, and metadata.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.content = "Mocked response"
    mock_response.response_metadata = {"key": "value"}
    # Set the mock to return the mock response object
    mock_invoke.return_value = mock_response
    llm = LangChainChatOpenAIModel(langchain_chatopenai_model_config)
    result = llm.invoke("Hello, world!")
    assert result.status == "success"
    assert result.content == "Mocked response"
    assert result.metadata == {"key": "value"}  # Update this to match expected metadata
    mock_invoke.assert_called_once_with("Hello, world!")


def test_langchain_chatopenaimodel_get_model(langchain_chatopenai_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LangChainChatOpenAIModel to verify it returns the model instance.
    """
    factory = ChatModel.create(langchain_chatopenai_model_config)
    result = factory.get_model()
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, ChatOpenAI)


@pytest.fixture
def langchain_azurechatopenai_model_config():
    """
    Mockup LangChain_AzureChatOpenAI model
    """
    return {
        "type": "LangChainAzureChatOpenAI",
        "model_name": "hpe-model",        
        "api_key": "your_api_key",
        "api_version": "your_api_version",
        "endpoint": "api_endpoint",
        "azure_deployment": "your_deployment"
    }


@patch.object(AzureChatOpenAI, 'invoke')
def test_langchain_azurechatopenai_model_invoke(
    mock_invoke, langchain_azurechatopenai_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LangChainAzureChatOpenAIModel to ensure it returns a result
    with the correct status and content.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.content = "Mocked response"
    mock_response.response_metadata = {"key": "value"}
    # Set the mock to return the mock response object
    mock_invoke.return_value = mock_response
    llm = LangChainAzureChatOpenAIModel(langchain_azurechatopenai_model_config)
    result = llm.invoke("Hello, world!")
    assert result.status == "success"
    assert result.content == "Mocked response"
    assert result.metadata == {"key": "value"}  # Update this to match expected metadata
    mock_invoke.assert_called_once_with("Hello, world!")


def test_langchain_azurechatopenai_model_get_model(langchain_azurechatopenai_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LangChainAzureChatOpenAIModel
    to ensure it returns the model instance.
    """
    factory = ChatModel.create(langchain_azurechatopenai_model_config)
    result = factory.get_model()
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, AzureChatOpenAI)


@pytest.fixture
def langchain_chatgooglegenai_model_config():
    """
    Mock configuration for LangChainChatGoogleGenAI model.
    """
    return {
        "type": "LangChainChatGoogleGenAI",
        "model_name": "gemini-1.5-pro",
        "api_key": "your_api_key",
        "temperature": 0.7,
        "max_tokens": 1024,
        "timeout": 30,
        "max_retries": 2,
    }


@patch.object(ChatGoogleGenerativeAI, 'invoke')
def test_langchain_chatgooglegenai_model_invoke(
    mock_invoke, langchain_chatgooglegenai_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LangChainChatGoogleGenAIModel to verify it returns a result
    with the correct status and content.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.content = "Mocked response"
    mock_response.response_metadata = {"key": "value"}
    # Set the mock to return the mock response object
    mock_invoke.return_value = mock_response
    llm = LangChainChatGoogleGenAIModel(langchain_chatgooglegenai_model_config)
    result = llm.invoke("Hello, world!")
    assert result.status == "success"
    assert result.content == "Mocked response"
    # If metadata is expected, you can include assertions for it here
    mock_invoke.assert_called_once_with("Hello, world!")


def test_langchain_chatgooglegenai_model_get_model(langchain_chatgooglegenai_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LangChainChatGoogleGenAIModel to verify
    it returns the model instance.
    """
    factory = ChatModel.create(langchain_chatgooglegenai_model_config)
    result = factory.get_model()
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, ChatGoogleGenerativeAI)


@pytest.fixture
def langchain_chatanthropic_model_config():
    """
    Mock configuration for LangChainChatAnthropic model.
    """
    return {
        "type": "LangChainChatAnthropic",
        "model_name": "claude-3-5-sonnet-20240620",
        "api_key": "your_api_key",
        "temperature": 0.7,
        "max_tokens": 1024,
        "timeout": 30,
        "max_retries": 2,
    }


@patch.object(ChatAnthropic, 'invoke')
def test_langchain_chatanthropic_model_invoke(
    mock_invoke, langchain_chatanthropic_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LangChainChatAnthropicModel to verify it returns a result
    with the correct status and content.
    """
    # Create a mock response
    mock_response = MagicMock()
    mock_response.content = "Mocked response"
    mock_response.response_metadata = {"key": "value"}
    # Set the mock to return the mock response
    mock_invoke.return_value = mock_response
    llm = LangChainChatAnthropicModel(langchain_chatanthropic_model_config)
    result = llm.invoke("Hello, world!")
    assert result.status == "success"
    assert result.content == "Mocked response"
    # If metadata is expected, you can include assertions for it here
    mock_invoke.assert_called_once_with("Hello, world!")


def test_langchain_chatanthropic_model_get_model(langchain_chatanthropic_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LangChainChatAnthropicModel to verify
    it returns the model instance.
    """
    factory = ChatModel.create(langchain_chatanthropic_model_config)
    result = factory.get_model()
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, ChatAnthropic)


@pytest.fixture
def langchain_chatmixtral_model_config():
    """
    Mock configuration for LangChainChatMixtral model.
    """
    return {
        "type": "LangChainChatMistralAI",
        "model_name": "mistral-large-latest",
        "api_key": "your_api_key",
        "temperature": 0.7,
        "max_retries": 2,
    }


@patch.object(ChatMistralAI, 'invoke')
def test_langchain_chatmixtral_model_invoke(
    mock_invoke, langchain_chatmixtral_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LangChainChatMistralAIModel to verify it returns a result
    with the correct status and content.
    """
    # Create a mock response
    mock_response = MagicMock()
    mock_response.content = "Mocked response"
    mock_response.response_metadata = {"key": "value"}
    # Set the mock to return the mock response
    mock_invoke.return_value = mock_response
    llm = LangChainChatMistralAIModel(langchain_chatmixtral_model_config)
    result = llm.invoke("Hello, world!")
    assert result.status == "success"
    assert result.content == "Mocked response"
    # If metadata is expected, you can include assertions for it here
    mock_invoke.assert_called_once_with("Hello, world!")


def test_langchain_chatmixtral_model_get_model(langchain_chatmixtral_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LangChainChatMistralAIModel to verify
    it returns the model instance.
    """
    factory = ChatModel.create(langchain_chatmixtral_model_config)
    result = factory.get_model()
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, ChatMistralAI)


@pytest.fixture
def langchain_chatnvidia_model_config():
    """
    Mock configuration for LangChainChatNvidia model.
    """
    return {
        "type": "LangChainChatNvidia",
        "model_name": "meta/llama-3.1-8b-instruct",
        "api_key": "your_api_key",
        "temperature": 0.7,
    }


@patch.object(ChatNVIDIA, 'invoke')
def test_langchain_chatnvidia_model_invoke(
    mock_invoke, langchain_chatnvidia_model_config):  # pylint: disable=W0621
    """
    Test the invoke method of LangChainChatNvidiaModel to verify it returns a result
    with the correct status and content.
    """
    # Create a mock response
    mock_response = MagicMock()
    mock_response.content = "Mocked response"
    mock_response.response_metadata = {"key": "value"}
    # Set the mock to return the mock response
    mock_invoke.return_value = mock_response
    # Initialize the model using the config
    model = LangChainChatNvidiaModel(langchain_chatnvidia_model_config)
    result = model.invoke("Hello, world!")
    # Check that the result status and content are correct
    assert result.status == "success"
    assert result.content == "Mocked response"
    # Check that the model was called with the correct input
    mock_invoke.assert_called_once_with("Hello, world!")


def test_langchain_chatnvidia_model_get_model(langchain_chatnvidia_model_config):  # pylint: disable=W0621
    """
    Test the get_model method of LangChainChatNvidiaModel to verify
    it returns the model instance.
    """
    model = ChatModel.create(langchain_chatnvidia_model_config)
    result = model.get_model()
    # Check that the result status is success and the model is returned
    assert result.status == "success"
    assert result.model is not None
    assert isinstance(result.model, ChatNVIDIA)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
