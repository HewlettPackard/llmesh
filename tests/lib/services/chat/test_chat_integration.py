#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration test for different ChatModel flavors using LangChain.

This test verifies that the ChatModel correctly handles requests for converting
a message into pirate language by invoking various LLMs (OpenAI, Google GenAI, Anthropic, etc.).
The API keys for each model are stored in environment variables.

To run this test, use:
    pytest -m "integration and chat"
"""

import os
import pytest
from langchain.schema import HumanMessage, SystemMessage
from athon.chat import ChatModel


model_configs = [
    {
        "type": "LangChainChatOpenAI",
        "model_name": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "https_verify": True,
    },
    {
        "type": "LangChainChatGoogleGenAI",
        "model_name": "gemini-1.5-pro",
        "api_key": os.getenv("GOOGLE_API_KEY"),
    },
    {
        "type": "LangChainChatAnthropic",
        "model_name": "claude-3-5-sonnet-20240620",
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
    },
    {
        "type": "LangChainChatMistralAI",
        "model_name": "mistral-large-latest",
        "api_key": os.getenv("MISTRAL_API_KEY"),
    },
    {
        "type": "LangChainChatNvidia",
        "model_name": "meta/llama-3.1-8b-instruct",
        "api_key": os.getenv("NVIDIA_API_KEY"),
    },
    {
        "type": "LangChainAzureChatOpenAI",
        "api_key": "",
        "azure_deployment": os.getenv("HPE_DEPLOYMENT"),
        "endpoint": os.getenv("HPE_ENDPOINT"),
        "api_version": os.getenv("HPE_API_VERSION"),
        "azure_jwt_server": os.getenv("HPE_JWT_SERVER"),
        "azure_client_id": os.getenv("HPE_CLIENT_ID"),
        "azure_client_secret": os.getenv("HPE_CLIENT_SECRET"),
        "azure_subscription_key": os.getenv("HPE_SUBSCRIPTION_KEY"),
        "https_verify": False,
    },
]

def should_skip_test(config):
    """
    Determine if a test should be skipped due to missing API key.
    """
    # For Azure OpenAI, check for required Azure-specific credentials
    if config["type"] == "LangChainAzureChatOpenAI":
        required_keys = ["azure_deployment", "endpoint", "api_version"]
        missing_keys = [key for key in required_keys if not config.get(key)]
        if missing_keys:
            return True
        # Check if we have either JWT or subscription key authentication
        has_jwt_auth = all(config.get(key) for key in ["azure_jwt_server", "azure_client_id", "azure_client_secret"])
        has_subscription_key = bool(config.get("azure_subscription_key"))
        return not (has_jwt_auth or has_subscription_key)

    # For all other models, simply check if API key is None
    return config.get("api_key") is None

@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.parametrize("config", model_configs)
def test_chat_model_invoke_pirate_language(config):
    """
    Test invoking the ChatModel to convert a message into pirate language
    using various model flavors (OpenAI, Google GenAI, Anthropic, etc.).
    """
    if should_skip_test(config):
        pytest.skip(f"Skipping test for {config['type']} due to missing API key")

    # Initialize the Chat Model with the provided configuration
    chat = ChatModel.create(config)
    # Define the prompts for the chat model
    prompts = [
        SystemMessage(content="Convert the message to pirate language using 'arr' as exclamation"),
        HumanMessage(content="Today is a sunny day and the sky is blue")
    ]
    # Invoke the model with the prompts
    result = chat.invoke(prompts)
    # Check that the invocation was successful
    assert result.status == "success", f"Chat invocation failed: {result.error_message}"
    assert result.content is not None, "The content of the result should not be None"
    assert "pirate" in result.content.lower() or "arr" in result.content.lower(), \
        f"Expected pirate-like response, but got: {result.content}"


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.parametrize("config", model_configs)
def test_chat_model_stream_pirate_language(config):
    """
    Test streaming with ChatModel to convert message into pirate language.
    """
    if should_skip_test(config):
        pytest.skip(f"Skipping test for {config['type']} due to missing API key")

    chat = ChatModel.create(config)
    prompts = [
        SystemMessage(content="Convert the message to pirate language using 'arr' as exclamation"),
        HumanMessage(content="Today is a sunny day and the sky is blue")
    ]
    chunks = list(chat.stream(prompts))
    # Join or check content as appropriate for your models
    joined_content = "".join(
        chunk for chunk in chunks if isinstance(chunk, str) or hasattr(chunk, "content"))
    assert "pirate" in joined_content.lower() or "arr" in joined_content.lower(), \
        f"Expected pirate-like response, but got: {joined_content}"


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
@pytest.mark.parametrize("config", model_configs)
async def test_chat_model_ainvoke_pirate_language(config):
    """
    Test async invoke with ChatModel for pirate language.
    """
    if should_skip_test(config):
        pytest.skip(f"Skipping test for {config['type']} due to missing API key")

    chat = ChatModel.create(config)
    prompts = [
        SystemMessage(content="Convert the message to pirate language using 'arr' as exclamation"),
        HumanMessage(content="Today is a sunny day and the sky is blue")
    ]
    result = await chat.ainvoke(prompts)
    assert result.status == "success", f"Chat ainvoke failed: {result.error_message}"
    assert result.content is not None, "The content of the result should not be None"
    assert "pirate" in result.content.lower() or "arr" in result.content.lower(), \
        f"Expected pirate-like response, but got: {result.content}"


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
@pytest.mark.parametrize("config", model_configs)
async def test_chat_model_astream_pirate_language(config):
    """
    Test async streaming with ChatModel for pirate language.
    """
    if should_skip_test(config):
        pytest.skip(f"Skipping test for {config['type']} due to missing API key")

    chat = ChatModel.create(config)
    prompts = [
        SystemMessage(content="Convert the message to pirate language using 'arr' as exclamation"),
        HumanMessage(content="Today is a sunny day and the sky is blue")
    ]
    collected_chunks = []
    async for chunk in chat.astream(prompts):
        # Many streaming APIs return objects, but sometimes just strings
        if hasattr(chunk, "content"):
            collected_chunks.append(chunk.content)
        elif isinstance(chunk, str):
            collected_chunks.append(chunk)
    joined_content = "".join(collected_chunks)
    assert "pirate" in joined_content.lower() or "arr" in joined_content.lower(), \
        f"Expected pirate-like response, but got: {joined_content}"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv', '-m', 'integration and chat'])
