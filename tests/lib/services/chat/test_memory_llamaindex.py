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


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
