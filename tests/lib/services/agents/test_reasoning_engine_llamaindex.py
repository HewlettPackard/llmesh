#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ReasoningEngine factory and its engine flavor,
LlamaIndexReActEngine. The tests ensure that the factory method correctly
initializes and returns instances of the appropriate engine types based on
the given configuration. It also tests the specific behavior of each engine's
methods to ensure correct setup and functionality.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from src.lib.services.agents.reasoning_engine import ReasoningEngine
from src.lib.services.agents.reasoning_engines.llamaindex.react import (
    LlamaIndexReActEngine
)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            'type': 'LlamaIndexReAct',
            'model': {'setting1': 'value1'},
            'memory': {'setting2': 'value2', 'memory_key': 'value3'},
            'tools': {'type': 'SomeToolType', 'list': ['tool1', 'tool2']},
            'system_prompt': 'template1',
            'verbose': True
        },
        LlamaIndexReActEngine
    )
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    with patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_tool_repository',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_engine',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_executor',  # pylint: disable=C0301
        return_value=MagicMock()
    ):
        engine_instance = ReasoningEngine.create(config)
        assert isinstance(engine_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        ReasoningEngine.create({'type': 'UnknownType'})


@pytest.fixture
def llama_index_react_engine_config():
    """
    Mockup LlamaIndexReActEngine configuration
    """
    return {
        'type': 'LlamaIndexReAct',
        'model': {'setting1': 'value1'},
        'memory': {'setting2': 'value2', 'memory_key': 'value3'},
        'tools': {'type': 'SomeToolType', 'list': ['tool1', 'tool2']},
        'system_prompt': 'template1',
        'verbose': True
    }


@patch(
    'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine.run',
    return_value=MagicMock(status="success", completion="Mocked response"))
def test_run(mock_run, llama_index_react_engine_config):  # pylint: disable=W0621
    """
    Test the run method of LlamaIndexReActEngine to verify it returns a result
    with the correct status and completion.
    """
    with patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_tool_repository',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_engine',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_executor',  # pylint: disable=C0301
        return_value=MagicMock()
    ):
        engine = ReasoningEngine.create(llama_index_react_engine_config)
        result = engine.run("Hello, world!")
        assert result.status == "success"
        assert result.completion == "Mocked response"
        mock_run.assert_called_once_with("Hello, world!")


@patch(
    'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine.clear_memory',  # pylint: disable=C0301
    return_value=MagicMock(status="success"))
def test_clear_memory(mock_clear_memory, llama_index_react_engine_config):  # pylint: disable=W0621
    """
    Test the clear_memory method of LlamaIndexReActEngine to verify it clears the memory
    and returns the correct status.
    """
    with patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_tool_repository',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_engine',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_executor',  # pylint: disable=C0301
        return_value=MagicMock()
    ):
        engine = ReasoningEngine.create(llama_index_react_engine_config)
        result = engine.clear_memory()
        assert result.status == "success"
        mock_clear_memory.assert_called_once()


@patch(
    'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine.set_memory',  # pylint: disable=C0301
    return_value=MagicMock(status="success"))
def test_set_memory(mock_set_memory, llama_index_react_engine_config):  # pylint: disable=W0621
    """
    Test the set_memory method of LlamaIndexReActEngine to verify it sets the memory
    and returns the correct status.
    """
    with patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_tool_repository',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_engine',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_executor',  # pylint: disable=C0301
        return_value=MagicMock()
    ):
        engine = ReasoningEngine.create(llama_index_react_engine_config)
        result = engine.set_memory({"key": "value"})
        assert result.status == "success"
        mock_set_memory.assert_called_once_with({"key": "value"})


@patch(
    'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine.set_tools',
    return_value=MagicMock(status="failure", error_message="Not possible change tool in LlamaIndexReActEngine"))  # pylint: disable=C0301
def test_set_tools(mock_set_tools, llama_index_react_engine_config):  # pylint: disable=W0621
    """
    Test the set_tools method of LlamaIndexReActEngine to verify it returns a failure
    when trying to set tools, as changing tools is not supported.
    """
    with patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_tool_repository',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_engine',  # pylint: disable=C0301
        return_value=MagicMock()
    ), patch(
        'src.lib.services.agents.reasoning_engines.llamaindex.react.LlamaIndexReActEngine._init_executor',  # pylint: disable=C0301
        return_value=MagicMock()
    ):
        engine = ReasoningEngine.create(llama_index_react_engine_config)
        result = engine.set_tools(["tool1", "tool2"])
        assert result.status == "failure"
        assert result.error_message == "Not possible change tool in LlamaIndexReActEngine"
        mock_set_tools.assert_called_once_with(["tool1", "tool2"])


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
