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
from langchain_core.vectorstores import VectorStoreRetriever
from src.lib.services.chat.memory import ChatMemory
from src.lib.services.chat.memories.langchain.chroma_store_retriever import (
    CustomVectorStoreRetrieverMemory
)
from src.lib.services.chat.memories.langchain.custom_remote import (
    CustomLangChainRemoteMemory,
    LangChainRemoteMemory
)
from src.lib.services.chat.memories.langchain.buffer import (
    LangChainBufferMemory
)
from src.lib.services.chat.memories.langchain.buffer_window import (
    LangChainBufferWindowMemory
)
from src.lib.services.chat.memories.langchain.chroma_store_retriever import (
    LangChainChromaStoreMemory
)
from src.lib.services.chat.memories.langchain.summary import (
    LangChainSummaryMemory
)


@pytest.mark.parametrize("config, expected_class", [
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
            "type": "LangChainBuffer",
            "memory_key": "chat_history",
            "return_messages": True
        },
        LangChainBufferMemory
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


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
