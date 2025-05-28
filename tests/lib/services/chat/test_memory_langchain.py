#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ChatMemory factory and its memory types,
including LangChainBufferMemory, LangChainChromaStoreMemory,
LangChainRemoteMemory, and LangChainSummaryMemory.
The tests ensure that the factory method correctly initializes and 
returns instances of the appropriate memory type based on the given configuration.
It also tests the specific behavior of each memory's methods to ensure correct setup
and functionality.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory
)
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.vectorstores import VectorStoreRetriever
from src.lib.services.chat.memory import ChatMemory
from src.lib.services.chat.memories.langchain.buffer import (
    LangChainBufferMemory
)
from src.lib.services.chat.memories.langchain.buffer_window import (
    LangChainBufferWindowMemory
)
from src.lib.services.chat.memories.langchain.summary import (
    LangChainSummaryMemory
)
from src.lib.services.chat.memories.langchain.chroma_store_retriever import (
    LangChainChromaStoreMemory,
    CustomVectorStoreRetrieverMemory
)
from src.lib.services.chat.memories.langchain.custom_remote import (
    CustomLangChainRemoteMemory,
    LangChainRemoteMemory
)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "LangChainBuffer",
            "memory_key": "chat_history",
            "return_messages": True
        },
        LangChainBufferMemory
    ),
    (
        {
            "type": "LangChainBufferWindow",
            "memory_key": "chat_history",
            "window": 5,
            "return_messages": True
        },
        LangChainBufferWindowMemory
    ),
    (
        {
            "type": "LangChainSummary",
            "memory_key": "chat_history",
            "llm_model": {
                "type": "LangChainChatOpenAI",
                "model_name":"gpt-4o",
                "api_key": "your_api_key"
            },
            "buffer": "Initial summary",
            "return_messages": True
        },
        LangChainSummaryMemory
    ),
    (
        {
            "type": "LangChainChromaStore",
            "memory_key": "chat_history",
            "persist_directory": "tests/lib/services/chat/data",
            "collection_name": "my_collection",
            "k": 5
        },
        LangChainChromaStoreMemory
    ),
    (
        {
            "type": "LangChainRemote",
            "memory_key": "chat_history",
            "base_url": "http://remote-memory-service",
            "timeout": 10,
            "cert_verify": True
        },
        LangChainRemoteMemory
    ),
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    memory_instance = ChatMemory.create(config)
    assert isinstance(memory_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        ChatMemory.create({"type": "UnknownType", "memory_key": "invalid"})


@pytest.fixture
def langchain_buffer_memory_config():
    """
    Mockup LangChain Buffer memory configuration
    """
    return {
        "type": "LangChainBuffer",
        "memory_key": "chat_history",
        "return_messages": True
    }


def test_langchain_buffer_memory_initialization(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test the initialization of LangChainBufferMemory to verify it sets up
    the correct memory instance with the configured settings.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    assert isinstance(memory.memory, ConversationBufferMemory)
    assert memory.memory.memory_key == "chat_history"
    assert memory.memory.return_messages is True


@patch.object(ConversationBufferMemory, 'clear', return_value=None)
def test_langchain_buffer_memory_clear(mock_clear, langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of LangChainBufferMemory to verify it clears the memory correctly.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    result = memory.clear()
    assert result.status == "success"
    mock_clear.assert_called_once()


def test_langchain_buffer_memory_get_memory(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test the get_memory method of LangChainBufferMemory to verify it returns the memory instance.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    result = memory.get_memory()
    assert result.status == "success"
    assert result.memory is not None
    assert isinstance(result.memory, ConversationBufferMemory)


def test_langchain_buffer_memory_save_human_message(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test saving a human message to LangChainBufferMemory.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    message = HumanMessage(content="Hello")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.chat_memory.messages[-1] == message


def test_langchain_buffer_memory_save_ai_message(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test saving an AI message to LangChainBufferMemory.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    message = AIMessage(content="Hello, how are you?")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.chat_memory.messages[-1] == message


def test_langchain_buffer_memory_save_invalid_message(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test saving an invalid message type to LangChainBufferMemory.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    invalid_message = {"content": "This is not a valid message object"}
    result = memory.save_message(invalid_message)
    assert result.status == "failure"
    assert "Error saving message" in result.error_message


def test_langchain_buffer_memory_get_messages(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages from LangChainBufferMemory.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    messages_to_save = [
        HumanMessage(content="Hi there!"),
        AIMessage(content="Hello! How can I assist you?")
    ]
    for msg in messages_to_save:
        memory.save_message(msg)
    result = memory.get_messages()
    assert result.status == "success"
    assert result.messages == messages_to_save


def test_langchain_buffer_memory_get_messages_with_limit(langchain_buffer_memory_config):  # pylint: disable=W0621
    """
    Test retrieving a limited number of messages from LangChainBufferMemory.
    """
    memory = ChatMemory.create(langchain_buffer_memory_config)
    messages_to_save = [
        HumanMessage(content="Message 1"),
        AIMessage(content="Message 2"),
        HumanMessage(content="Message 3")
    ]
    for msg in messages_to_save:
        memory.save_message(msg)
    result = memory.get_messages(limit=2)
    assert result.status == "success"
    assert result.messages == messages_to_save[-2:]


@pytest.fixture
def langchain_buffer_window_memory_config():
    """
    Mockup LangChain Buffer Window memory configuration
    """
    return {
        "type": "LangChainBufferWindow",
        "memory_key": "chat_history",
        "window": 5,
        "return_messages": True
    }


def test_langchain_buffer_window_memory_initialization(langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test the initialization of LangChainBufferWindowMemory to verify it sets up
    the correct memory instance with the configured settings.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    assert isinstance(memory.memory, ConversationBufferWindowMemory)
    assert memory.memory.memory_key == "chat_history"
    assert memory.memory.return_messages is True


@patch.object(ConversationBufferWindowMemory, 'clear', return_value=None)
def test_langchain_buffer_window_memory_clear(mock_clear, langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of LangChainBufferMemory to verify it clears the memory correctly.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    result = memory.clear()
    assert result.status == "success"
    mock_clear.assert_called_once()


def test_langchain_buffer_window_memory_get_memory(langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test the get_memory method of LangChainBufferMemory to verify it returns the memory instance.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    result = memory.get_memory()
    assert result.status == "success"
    assert result.memory is not None
    assert isinstance(result.memory, ConversationBufferWindowMemory)


def test_langchain_buffer_window_memory_save_human_message(langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test saving a human message to LangChainBufferWindowMemory.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    message = HumanMessage(content="Hello")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.chat_memory.messages[-1] == message


def test_langchain_buffer_window_memory_save_ai_message(langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test saving an AI message to LangChainBufferWindowMemory.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    message = AIMessage(content="Hello, how are you?")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.chat_memory.messages[-1] == message


def test_langchain_buffer_window_memory_save_invalid_message(langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test saving an invalid message type to LangChainBufferWindowMemory.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    invalid_message = {"content": "This is not a valid message object"}
    result = memory.save_message(invalid_message)
    assert result.status == "failure"
    assert "Error saving message" in result.error_message


def test_langchain_buffer_window_memory_get_messages(langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages from LangChainBufferWindowMemory.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    messages_to_save = [
        HumanMessage(content="Hi there!"),
        AIMessage(content="Hello! How can I assist you?")
    ]
    for msg in messages_to_save:
        memory.save_message(msg)
    result = memory.get_messages()
    assert result.status == "success"
    assert result.messages == messages_to_save


def test_langchain_buffer_window_memory_get_messages_with_limit(
        langchain_buffer_window_memory_config):  # pylint: disable=W0621
    """
    Test retrieving a limited number of messages from LangChainBufferWindowMemory.
    """
    memory = ChatMemory.create(langchain_buffer_window_memory_config)
    messages_to_save = [
        HumanMessage(content="Message 1"),
        AIMessage(content="Message 2"),
        HumanMessage(content="Message 3")
    ]
    for msg in messages_to_save:
        memory.save_message(msg)
    result = memory.get_messages(limit=2)
    assert result.status == "success"
    assert result.messages == messages_to_save[-2:]


@pytest.fixture
def langchain_summary_memory_config():
    """
    Mockup LangChain Summary memory configuration
    """
    return {
        "type": "LangChainSummary",
        "memory_key": "chat_history",
        "llm_model": {
            "type": "LangChainChatOpenAI",
            "model_name":"gpt-4o",
            "api_key": "your_api_key"
        },
        "buffer": "Initial summary",
        "return_messages": True
    }


def test_langchain_summary_memory_initialization(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test the initialization of LangChainSummaryMemory to verify
    it sets up the correct memory instance with the configured settings.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    assert isinstance(memory.memory, ConversationSummaryMemory)
    assert memory.memory.memory_key == "chat_history"
    assert memory.memory.return_messages is True


@patch.object(ConversationSummaryMemory, 'clear', return_value=None)
def test_langchain_summary_memory_clear(mock_clear, langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of LangChainSummaryMemory to verify it clears the memory correctly.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    result = memory.clear()
    assert result.status == "success"
    mock_clear.assert_called_once()


def test_langchain_summary_memory_get_memory(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test the get_memory method of LangChainSummaryMemory to verify it returns the memory instance.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    result = memory.get_memory()
    assert result.status == "success"
    assert result.memory is not None
    assert isinstance(result.memory, ConversationSummaryMemory)


def test_langchain_summary_memory_save_human_message(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test saving a human message to LangChainSummaryMemory.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    message = HumanMessage(content="Hello from user")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.chat_memory.messages[-1] == message


def test_langchain_summary_memory_save_ai_message(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test saving an AI message to LangChainSummaryMemory.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    message = AIMessage(content="Hello from AI")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.chat_memory.messages[-1] == message


def test_langchain_summary_memory_save_invalid_message(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test saving an invalid message type to LangChainSummaryMemory.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    invalid_message = {"content": "Not a valid message object"}
    result = memory.save_message(invalid_message)
    assert result.status == "failure"
    assert "Error saving message" in result.error_message


def test_langchain_summary_memory_get_messages(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages from LangChainSummaryMemory.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    messages_to_save = [
        HumanMessage(content="Hi there!"),
        AIMessage(content="Hello! How can I help?")
    ]
    for msg in messages_to_save:
        memory.save_message(msg)
    result = memory.get_messages()
    assert result.status == "success"
    # Messages list should contain the ones just saved (after any initial summary, if any)
    assert result.messages[-2:] == messages_to_save


def test_langchain_summary_memory_get_messages_with_limit(langchain_summary_memory_config):  # pylint: disable=W0621
    """
    Test retrieving a limited number of messages from LangChainSummaryMemory.
    """
    memory = ChatMemory.create(langchain_summary_memory_config)
    messages_to_save = [
        HumanMessage(content="Msg 1"),
        AIMessage(content="Msg 2"),
        HumanMessage(content="Msg 3")
    ]
    for msg in messages_to_save:
        memory.save_message(msg)
    result = memory.get_messages(limit=2)
    assert result.status == "success"
    assert result.messages == messages_to_save[-2:]


def test_langchain_summary_memory_get_summary_string():
    """
    Test retrieving only the summary string when return_messages is False.
    """
    config = {
        "type": "LangChainSummary",
        "memory_key": "chat_history",
        "llm_model": {
            "type": "LangChainChatOpenAI",
            "model_name": "gpt-4o",
            "api_key": "your_api_key"
        },
        "buffer": "Initial summary",
        "return_messages": False
    }
    memory = ChatMemory.create(config)
    result = memory.get_messages()
    assert result.status == "success"
    assert result.messages == "Initial summary"


@pytest.fixture
def langchain_chroma_store_memory_config():
    """
    Mockup LangChain Chroma Store memory configuration
    """
    return {
        "type": "LangChainChromaStore",
        "memory_key": "chat_history",
        "persist_directory": "tests/lib/services/chat/data",
        "collection_name": "my_collection",
        "k": 5
    }


@patch('langchain_community.vectorstores.Chroma')
def test_langchain_chroma_store_memory_initialization(
    mock_chroma, langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test the initialization of LangChainChromaStoreMemory to verify
    it sets up the correct memory instance with the configured settings.
    """
    mock_chroma_instance = MagicMock()
    mock_chroma.return_value = mock_chroma_instance
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    assert isinstance(memory.memory, CustomVectorStoreRetrieverMemory)
    assert isinstance(memory.retriever, VectorStoreRetriever)


@patch.object(CustomVectorStoreRetrieverMemory, 'clear', return_value=None)
def test_langchain_chroma_store_memory_clear(mock_clear, langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of LangChainChromaStoreMemory to verify it clears the memory correctly.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    result = memory.clear()
    assert result.status == "success"
    mock_clear.assert_called_once()


def test_langchain_chroma_store_memory_get_memory(langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test the get_memory method of LangChainChromaStoreMemory
    to verify it returns the memory instance.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    result = memory.get_memory()
    assert result.status == "success"
    assert result.memory is not None
    assert isinstance(result.memory, CustomVectorStoreRetrieverMemory)


@patch('src.lib.services.chat.memories.langchain.chroma_store_retriever.CustomVectorStoreRetrieverMemory.save_context')  # pylint: disable=C0301
def test_langchain_chroma_store_memory_save_message(
    mock_save_context, langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test saving a valid message pair to LangChainChromaStoreMemory.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    human = HumanMessage(content="Hi, can you help me?")
    ai = AIMessage(content="Of course! How can I assist?")
    result = memory.save_message([human, ai])
    assert result.status == "success"
    mock_save_context.assert_called_once()
    # The exact call arguments are: ({}, {"input": human.content, "output": ai.content})


def test_langchain_chroma_store_memory_save_invalid_message_type(
        langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test saving an invalid message type (not a [HumanMessage, AIMessage] list) 
    to LangChainChromaStoreMemory.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    invalid_message = "Just a string"
    result = memory.save_message(invalid_message)
    assert result.status == "failure"
    assert (
        "Vector store memory expects a [HumanMessage, AIMessage] list/tuple."
        in result.error_message
    )


def test_langchain_chroma_store_memory_save_invalid_message_length(
        langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test saving a message list of wrong length to LangChainChromaStoreMemory.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    # Only one message instead of two
    one_message = [HumanMessage(content="Only one")]
    result = memory.save_message(one_message)
    assert result.status == "failure"
    assert (
        "Vector store memory expects a [HumanMessage, AIMessage] list/tuple." 
        in result.error_message
    )


@patch('src.lib.services.chat.memories.langchain.chroma_store_retriever.CustomVectorStoreRetrieverMemory.load_memory_variables')  # pylint: disable=C0301
def test_langchain_chroma_store_memory_get_messages(
    mock_load_memory_variables, langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages from LangChainChromaStoreMemory.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    # Mock messages to return (simulate HumanMessage/AIMessage objects)
    messages = [
        HumanMessage(content="Hi!"),
        AIMessage(content="Hello, how can I help?")
    ]
    # Simulate .load_memory_variables() returns {memory_key: messages}
    mock_load_memory_variables.return_value = {"chat_history": messages}
    result = memory.get_messages()
    assert result.status == "success"
    assert result.messages == messages


@patch('src.lib.services.chat.memories.langchain.chroma_store_retriever.CustomVectorStoreRetrieverMemory.load_memory_variables')  # pylint: disable=C0301
def test_langchain_chroma_store_memory_get_messages_with_inputs(
    mock_load_memory_variables, langchain_chroma_store_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages with a custom inputs dict.
    """
    memory = ChatMemory.create(langchain_chroma_store_memory_config)
    messages = [
        HumanMessage(content="What's the weather?"),
        AIMessage(content="It's sunny today!")
    ]
    mock_load_memory_variables.return_value = {"chat_history": messages}
    inputs = {"query": "weather"}
    result = memory.get_messages(inputs=inputs)
    assert result.status == "success"
    assert result.messages == messages
    mock_load_memory_variables.assert_called_once_with(inputs)


@pytest.fixture
def remote_memory_config():
    """
    Mockup configuration for CustomLangChainRemoteMemory
    """
    return {
        "type": "LangChainRemote",
        "base_url": "http://remote-memory-service",
        "memory_key": "chat_history",
        "timeout": 10,
        "cert_verify": True
    }


class MockMessageManager:
    "Mock class"
    def convert_to_messages(self, json_data):  # pylint: disable=W0613
        "Mock Function"
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.prompts = ["Mocked prompt"]
        return mock_result
    def convert_to_strings(self, inputs):  # pylint: disable=W0613
        "Mock Function"
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.prompts = ["Mocked string"]
        return mock_result


@patch('src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create')
@patch('src.lib.services.chat.memories.langchain.custom_remote.requests.post')
def test_custom_remote_memory_load(mock_post, mock_message_manager_create, remote_memory_config):  # pylint: disable=W0621
    """
    Test the load_memory_variables method of CustomLangChainRemoteMemory.
    """
    mock_message_manager_create.return_value = MockMessageManager()
    mock_post.return_value.json.return_value = {"data": "mock_data"}
    mock_post.return_value.raise_for_status = MagicMock()
    memory = CustomLangChainRemoteMemory(remote_memory_config)
    result = memory.load_memory_variables("inputs")
    assert result == ["Mocked prompt"]
    mock_post.assert_called_once_with(
        'http://remote-memory-service/load',
        json={'inputs': 'inputs'},
        verify=True,
        timeout=10
    )


@patch('src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create')
@patch('src.lib.services.chat.memories.langchain.custom_remote.requests.post')
def test_custom_remote_memory_save(mock_post, mock_message_manager_create, remote_memory_config):  # pylint: disable=W0621
    """
    Test the save_context method of CustomLangChainRemoteMemory.
    """
    mock_message_manager_create.return_value = MockMessageManager()
    mock_post.return_value.raise_for_status = MagicMock()
    memory = CustomLangChainRemoteMemory(remote_memory_config)
    memory.save_context("inputs", "outputs")
    mock_post.assert_called_once_with(
        'http://remote-memory-service/store',
        json={'inputs': ['Mocked string'], 'outputs': 'outputs'},
        verify=True,
        timeout=10
    )


@patch('src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create')
@patch('src.lib.services.chat.memories.langchain.custom_remote.requests.post')
def test_custom_remote_memory_clear(mock_post, mock_message_manager_create, remote_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of CustomLangChainRemoteMemory.
    """
    mock_message_manager_create.return_value = MockMessageManager()
    mock_post.return_value.raise_for_status = MagicMock()
    memory = CustomLangChainRemoteMemory(remote_memory_config)
    memory.clear()
    mock_post.assert_called_once_with(
        'http://remote-memory-service/clear',
        json=None,
        verify=True,
        timeout=10
    )


@pytest.fixture
def langchain_remote_memory_config():
    """
    Mockup LangChain Remote memory configuration
    """
    return {
        "type": "LangChainRemote",
        "memory_key": "chat_history",
        "base_url": "http://remote-memory-service",
        "timeout": 10,
        "cert_verify": True
    }


@patch.object(CustomLangChainRemoteMemory, 'load_memory_variables', return_value="Mocked response")
def test_langchain_remote_memory_load(mock_load, langchain_remote_memory_config):  # pylint: disable=W0621
    """
    Test the load_memory_variables method of LangChainRemoteMemory
    to verify it loads memory variables correctly.
    """
    memory = ChatMemory.create(langchain_remote_memory_config)
    result = memory.memory.load_memory_variables("inputs")
    assert result == "Mocked response"
    mock_load.assert_called_once_with("inputs")


@patch.object(CustomLangChainRemoteMemory, 'clear', return_value=None)
def test_langchain_remote_memory_clear(mock_clear, langchain_remote_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of LangChainRemoteMemory to verify it clears the memory correctly.
    """
    memory = ChatMemory.create(langchain_remote_memory_config)
    result = memory.clear()
    assert result.status == "success"
    mock_clear.assert_called_once()


def test_langchain_remote_memory_get_memory(langchain_remote_memory_config):  # pylint: disable=W0621
    """
    Test the get_memory method of LangChainRemoteMemory to verify it returns the memory instance.
    """
    memory = ChatMemory.create(langchain_remote_memory_config)
    result = memory.get_memory()
    assert result.status == "success"
    assert result.memory is not None
    assert isinstance(result.memory, CustomLangChainRemoteMemory)


@patch("src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create")
@patch.object(CustomLangChainRemoteMemory, "save_context")
def test_langchain_remote_memory_save_valid_message_pair(
    mock_save_context, mock_create_manager, remote_memory_config):  # pylint: disable=W0621
    """
    Test saving a valid [HumanMessage, AIMessage] pair to remote memory.
    """
    mock_create_manager.return_value = MockMessageManager()
    memory = LangChainRemoteMemory(remote_memory_config)
    message = [HumanMessage(content="Hello"), AIMessage(content="Hi there!")]
    result = memory.save_message(message)
    assert result.status == "success"
    mock_save_context.assert_called_once()


@patch("src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create")
def test_langchain_remote_memory_save_invalid_message_structure(
    mock_create_manager, remote_memory_config):  # pylint: disable=W0621
    """
    Test saving an invalid message structure should fail.
    """
    mock_create_manager.return_value = MockMessageManager()
    memory = LangChainRemoteMemory(remote_memory_config)
    invalid_message = {"text": "This is not a valid message structure"}
    result = memory.save_message(invalid_message)
    assert result.status == "failure"
    assert "message pair" in result.error_message or "Remote memory expects" in result.error_message


@patch("src.lib.services.chat.memories.langchain.custom_remote.CustomLangChainRemoteMemory.load_memory_variables")  # pylint: disable=C0301
@patch("src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create")
def test_langchain_remote_memory_get_messages_from_remote_memory(
    mock_create_manager, mock_load, remote_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages from remote memory.
    """
    mock_create_manager.return_value = MockMessageManager()
    # Return two real message objects from the mocked memory
    mock_load.return_value = [
        HumanMessage(content="Hello from user"),
        AIMessage(content="Hello from assistant")
    ]
    memory = LangChainRemoteMemory(remote_memory_config)
    result = memory.get_messages()
    assert result.status == "success"
    assert isinstance(result.messages, list)
    assert len(result.messages) == 2
    assert all(isinstance(msg, (HumanMessage, AIMessage)) for msg in result.messages)


@patch("src.lib.services.chat.memories.langchain.custom_remote.CustomLangChainRemoteMemory.load_memory_variables")  # pylint: disable=C0301
@patch("src.lib.services.chat.memories.langchain.custom_remote.MessageManager.create")
def test_get_messages_with_limit(mock_create_manager, mock_load, remote_memory_config):  # pylint: disable=W0621
    """
    Test retrieving a limited number of messages from remote memory.
    """
    # Use dummy message manager — not relevant here since we patch `load_memory_variables`
    mock_create_manager.return_value = MagicMock()
    # Return a valid list of BaseMessage objects
    mock_load.return_value = [
        HumanMessage(content="Hi"),
        AIMessage(content="Hello!"),
        HumanMessage(content="How are you?")
    ]
    memory = ChatMemory.create(remote_memory_config)
    result = memory.get_messages(limit=1)
    assert result.status == "success"
    assert len(result.messages) == 1
    assert isinstance(result.messages[0], (HumanMessage, AIMessage))


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
