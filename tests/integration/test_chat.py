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


@pytest.mark.parametrize("config", [
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
])

@pytest.mark.integration
@pytest.mark.chat
def test_chat_model_invoke_pirate_language(config):
    """
    Test invoking the ChatModel to convert a message into pirate language
    using various model flavors (OpenAI, Google GenAI, Anthropic, etc.).
    """
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


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv', '-m', 'integration and chat'])
