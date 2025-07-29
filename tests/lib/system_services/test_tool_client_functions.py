#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The tests ensure that the AthonTool class properly initializes with valid configurations and
handles invalid configurations by raising appropriate exceptions. These tests help in verifying
that the configuration requirements for the tool are enforced correctly, which is crucial for
ensuring stability and predictable behavior in production environments.
"""

import os
from unittest.mock import MagicMock, patch
import pytest
from flask import Flask
from src.lib.tool_api.tool_client import AthonTool
from src.lib.services.core.log import Logger


def test_athon_tool_initialization():
    """
    Test Initialization and Configuration Validation
    """
    valid_config = {
        'tool': {
            'name': 'TestTool',
            'function': 'lambda x: x',
            'description': 'A simple test tool',
            'arguments': [{'name': 'param', 'type': 'str', 'description': 'A parameter'}]
        }
    }
    logger = Logger().get_logger()
    tool = AthonTool(valid_config, logger)
    assert tool.config == valid_config, "Configuration should be stored correctly"


def test_invalid_config():
    """
    Test initialization with invalid configuration
    """
    invalid_configs = [
        'somestring', # Not a dict
        {},  # Empty config
        {'tool': None},  # tool not a dict
        {'tool': {'function': 'Test', 'description': 'Test'}},  # Missing name
        {'tool': {'name': 'Test', 'description': 'Test'}},  # Missing function
        {'tool': {'name': 'Test','function': 'Test'}},  # Missing description
    ]
    logger = Logger().get_logger()
    for config in invalid_configs:
        with pytest.raises(ValueError) as excinfo:
            AthonTool(config, logger)
        print(excinfo.value) # Can be seen passing "-s" flag to pytest


def test_decorator_functionality():
    """
    Test Decorator Behavior
    """
    config = {
        'tool': {
            'name': 'TestTool',
            'function': 'lambda x: x',
            'description': 'A simple test tool',
            'arguments': [{'name': 'x', 'type': 'int', 'description': 'A number'}]
        }
    }
    logger = MagicMock()
    tool = AthonTool(config, logger)
    @tool
    def sample_function(x):
        return x * 2
    assert sample_function(3) == 6, "The decorated function should return double the input"


def test_invoke():
    """
    Test Function Invocation
    """
    config = {
        'tool': {
            'name': 'TestTool',
            'function': 'lambda x: x',
            'description': 'A simple test tool',
            'arguments': [{'name': 'x', 'type': 'int', 'description': 'A number'}]
        }
    }
    logger = MagicMock()
    tool = AthonTool(config, logger)
    @tool
    def sample_function(x):
        return x * 2
    assert tool.invoke(3) == 6, \
         "Invoke should call the function correctly and return the expected result"


def test_get_manifest():
    """
    Test Manifest Retrieval
    """
    config = {
        'tool': {
            'name': 'TestTool',
            'function': 'lambda x: x',
            'description': 'Mocked description',
            'arguments': [
                {'name': 'x', 'type': 'int', 'description': 'Mocked description'}
            ]
        },
        'prompts': {
            'description_key': 'A simple test tool',
            'arg_description_key': 'A number'
        }
    }
    logger = MagicMock()
    tool = AthonTool(config, logger)
    # Setting up the tool class
    @tool
    def sample_function(x):
        return x * 2
    manifest = tool.get_manifest()
    # Assertions to verify the manifest and mock calls
    assert manifest['description'] == 'Mocked description', \
        "Manifest description should be mocked"
    assert all(arg['description'] == 'Mocked description' for arg in manifest['arguments']), \
        "Argument descriptions should be mocked"


def test_run_app():
    """
    Simulate Web Application
    """
    config = {
        'tool': {
            'name': 'TestTool',
            'function': 'lambda x: x',
            'description': 'A simple test tool',
            'arguments': [{'name': 'x', 'type': 'int', 'description': 'A number'}],
            'webapp': {'ip': '127.0.0.1', 'port': 5000}
        }
    }
    logger = MagicMock()
    tool = AthonTool(config, logger)
    with patch.object(Flask, 'run', return_value=None) as mock_run:
        app = tool.run_app(test=True)
        assert app is not None, "The Flask app should be initialized for testing"
        mock_run.assert_not_called()  # Ensure that Flask.run is not called during tests


@pytest.fixture
def mock_minimal_config():
    """
    Returns a minimal valid tool config, used to patch Config.get_settings.
    """
    return {
        "tool": {
            "name": "DefaultTool",
            "function": "default_func",
            "description": "A default tool"
        }
    }

def test_no_config_no_logger(mock_minimal_config):  # pylint: disable=W0621
    """
    Test that AthonTool can initialize without explicitly passing config or logger.
    We patch out file-system calls so it doesn't rely on an actual config file.
    """
    with patch(
        "src.lib.services.core.config.Config.get_settings",
        return_value=mock_minimal_config):
        tool = AthonTool()  # No config, no logger
        assert tool.config["tool"]["name"] == "DefaultTool", \
            "AthonTool should load or generate a default config when none is provided."
        assert tool.logger is not None, \
            "AthonTool should create a default logger when none is provided."


def test_no_logger_but_valid_config():
    """
    Test that AthonTool can initialize with a valid config but no logger.
    """
    config = {
        "tool": {
            "name": "MyTool",
            "function": "my_func",
            "description": "Just a test tool"
        }
    }
    tool = AthonTool(config=config)  # valid config, no logger
    assert tool.config["tool"]["name"] == "MyTool"
    assert tool.logger is not None, \
        "AthonTool should create a default logger when none is provided."


def test_no_config_but_logger(mock_minimal_config):  # pylint: disable=W0621
    """
    Test that AthonTool can initialize with a logger but no config.
    """
    mock_logger = MagicMock()
    with patch(
        "src.lib.services.core.config.Config.get_settings",
        return_value=mock_minimal_config):
        tool = AthonTool(logger=mock_logger)  # no config, but we have a logger
        assert tool.logger == mock_logger, "AthonTool should use the provided logger."
        assert tool.config["tool"]["name"] == "DefaultTool", \
            "AthonTool should fall back to a default config behavior when config is None."


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
