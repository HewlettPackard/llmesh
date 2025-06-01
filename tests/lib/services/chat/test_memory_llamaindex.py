#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ChatMemory factory and its memory types,
including LlamaIndexBufferMemory.
The tests ensure that the factory method correctly initializes and 
returns instances of the appropriate memory type based on the given configuration.
It also tests the specific behavior of each memory's methods to ensure correct setup
and functionality.
"""

import os
from unittest.mock import patch
import pytest
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer
from src.lib.services.chat.memory import ChatMemory
from src.lib.services.chat.memories.llamaindex.buffer import (
    LlamaIndexBufferMemory
)

@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "LlamaIndexBuffer",
            "memory_key": "chat_history"
        },
        LlamaIndexBufferMemory
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
def llamaindex_buffer_memory_config():
    """
    Mockup LLamaIndex Buffer memory configuration
    """
    return {
        "type": "LlamaIndexBuffer",
        "memory_key": "chat_history"
    }


def test_llamaindex_buffer_memory_initialization(llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test the initialization of LlamaIndexBufferMemory to verify it sets up
    the correct memory instance with the configured settings.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    assert isinstance(memory.memory, ChatMemoryBuffer)
    assert memory.memory.chat_store_key == "chat_history"


@patch.object(ChatMemoryBuffer, 'reset', return_value=None)
def test_lllamaindex_buffer_memory_clear(mock_clear, llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test the clear method of LlamaIndexBufferMemory to verify it clears the memory correctly.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    result = memory.clear()
    assert result.status == "success"
    mock_clear.assert_called_once()


def test_llamaindex_buffer_memory_get_memory(llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test the get_memory method of LlamaIndexBufferMemory to verify it returns the memory instance.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    result = memory.get_memory()
    assert result.status == "success"
    assert result.memory is not None
    assert isinstance(result.memory, ChatMemoryBuffer)


def test_llamaindex_buffer_memory_save_valid_message(llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test saving a valid ChatMessage to LlamaIndexBufferMemory.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    message = ChatMessage(role=MessageRole.USER, content="Hello!")
    result = memory.save_message(message)
    assert result.status == "success"
    assert memory.memory.get()[-1].content == "Hello!"


def test_llamaindex_buffer_memory_save_invalid_message_type(llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test saving an invalid message type to LlamaIndexBufferMemory.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    invalid_message = {"role": "user", "content": "This won't work"}
    result = memory.save_message(invalid_message)
    assert result.status == "failure"
    assert "ChatMessage" in result.error_message


def test_llamaindex_buffer_memory_get_messages(llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test retrieving messages from LlamaIndexBufferMemory.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    user_msg = ChatMessage(role=MessageRole.USER, content="What's the weather?")
    bot_msg = ChatMessage(role=MessageRole.ASSISTANT, content="Sunny and clear.")
    memory.save_message(user_msg)
    memory.memory.put(bot_msg)  # directly using memory to simulate turn
    result = memory.get_messages()
    assert result.status == "success"
    assert isinstance(result.messages, list)
    assert len(result.messages) == 2
    assert result.messages[0].role == MessageRole.USER
    assert result.messages[1].role == MessageRole.ASSISTANT


def test_llamaindex_buffer_memory_get_messages_with_limit(llamaindex_buffer_memory_config):  # pylint: disable=W0621
    """
    Test retrieving a limited number of messages from LlamaIndexBufferMemory.
    """
    memory = ChatMemory.create(llamaindex_buffer_memory_config)
    messages = [
        ChatMessage(role=MessageRole.USER, content="Msg 1"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Msg 2"),
        ChatMessage(role=MessageRole.USER, content="Msg 3")
    ]
    for msg in messages:
        memory.memory.put(msg)
    result = memory.get_messages(limit=2)
    assert result.status == "success"
    assert len(result.messages) == 2
    assert result.messages[-1].content == "Msg 3"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
