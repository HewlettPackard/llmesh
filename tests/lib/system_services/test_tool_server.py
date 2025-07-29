#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains unit tests for the `ToolDiscovery` class in the
`lib.system.tool_server` module. These tests validate the 
functionality of loading, parsing, and validating tool manifests, both locally 
and remotely.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError
from langchain.tools import StructuredTool
from src.lib.tool_api.tool_server import ToolDiscovery


@pytest.fixture
def tool_discovery():
    """
    Fixture to provide an instance of ToolDiscovery.
    """
    return ToolDiscovery()

@pytest.fixture
def sample_manifest():
    """
    Fixture to provide a sample tool manifest for testing purposes.
    """
    return {
        'name': 'SampleTool',
        'arguments': [
            {'name': 'param1', 'type': 'str', 'description': 'A string parameter'},
            {'name': 'param2', 'type': 'int', 'description': 'An integer parameter',
             'default': 10}
        ],
        'function': lambda param1, param2: f"Params: {param1}, {param2}",
        'description': 'A sample tool for testing',
        'return_direct': True
    }

def test_create_args_schema(tool_discovery, sample_manifest):  # pylint: disable=W0621
    """
    Test the creation of an argument schema based on the provided tool manifest.
    Validates the schema class name and the presence of specified fields.
    """
    schema = tool_discovery._create_args_schema(  # pylint: disable=W0212
        sample_manifest['name'],
        sample_manifest['arguments'])
    assert schema.__name__ == 'SampleToolArgsSchema'
    assert 'param1' in schema.model_fields
    assert 'param2' in schema.model_fields


@patch('importlib.util.spec_from_file_location')
@patch('importlib.util.module_from_spec')
def test_load_local_tool(
        mock_module_from_spec,
        mock_spec_from_file_location,
        tool_discovery,  # pylint: disable=W0621
        sample_manifest):  # pylint: disable=W0621
    """
    Test loading a local tool from a specified file path.
    Mocks the importlib functions to simulate loading a Python module.
    Verifies that the tool and interface are correctly loaded.
    """
    # Mock the imported module's main function to return the sample manifest
    mock_spec = MagicMock()
    mock_spec_from_file_location.return_value = mock_spec
    mock_module = MagicMock()
    mock_module.main.return_value = sample_manifest
    mock_module_from_spec.return_value = mock_module
    tool, interface = tool_discovery._load_local_tool('some_path')  # pylint: disable=W0212
    assert tool.name == 'SampleTool'
    assert isinstance(tool, StructuredTool)
    assert interface is None


@patch('requests.get')
def test_fetch_remote_manifest(mock_get, tool_discovery, sample_manifest):  # pylint: disable=W0621
    """
    Test fetching a remote tool manifest from a URL.
    Mocks the requests.get call to return a fake manifest.
    Verifies that the manifest is correctly fetched and matches the expected structure.
    """
    # Mock the requests.get response to return a fake manifest
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = sample_manifest
    mock_get.return_value = mock_response
    manifest = tool_discovery._fetch_remote_manifest('http://example.com/manifest')  # pylint: disable=W0212
    assert manifest == sample_manifest


@patch('requests.post')
def test_load_remote_tool(mock_post, tool_discovery, sample_manifest):  # pylint: disable=W0621
    """
    Test loading a remote tool by posting to its endpoint and fetching its manifest.
    Mocks the requests.post call and verifies that the tool and interface 
    are correctly loaded.
    Also checks that the tool's function returns the expected response.
    """
    # Mock the POST request to the tool's endpoint
    mock_post_response = MagicMock()
    mock_post_response.ok = True
    mock_post_response.text = 'Remote Tool Response'
    mock_post.return_value = mock_post_response
    # Manually set up the expected response for fetching the remote manifest
    with patch.object(tool_discovery, '_fetch_remote_manifest',
                      return_value=sample_manifest):
        tool, interface = tool_discovery._load_remote_tool('http://example.com/')  # pylint: disable=W0212
    assert tool.name == 'SampleTool'
    assert isinstance(tool, StructuredTool)
    assert interface is None
    assert tool.func() == 'Remote Tool Response'


def test_invalid_manifest(tool_discovery):  # pylint: disable=W0621
    """
    Test handling of an invalid tool manifest with an unsupported argument type.
    Verifies that a NameError is raised when attempting to create the tool.
    """
    invalid_manifest = {
        'name': 'InvalidTool',
        'arguments': [
            {'name': 'param1', 'type': 'nonexistent_type'}
        ],
        'function': lambda param1: f"Param: {param1}",
        'description': 'A tool with an invalid type'
    }
    with pytest.raises(NameError):
        tool_discovery._create_tool_from_local_manifest(invalid_manifest)  # pylint: disable=W0212


@patch('requests.get')
def test_get_settings_remote_tool(mock_get, tool_discovery):  # pylint: disable=W0621
    """
    Test fetching settings from a remote tool's settings endpoint.
    Mocks the requests.get call to return a sample configuration response.
    """
    # Define a sample configuration response
    sample_settings = {
        'setting1': 'value1',
        'setting2': 'value2'
    }
    # Mock the GET request to the tool's settings endpoint
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = sample_settings
    mock_get.return_value = mock_response
    # Invoke the get_settings method with a URL
    tool_reference = 'http://example.com'
    settings = tool_discovery.get_settings(tool_reference)
    # Assertions to validate the response
    mock_get.assert_called_once_with(
        f"{tool_reference}/settings",
        timeout=tool_discovery.config.timeout,
        verify=tool_discovery.config.cert_verify
    )
    assert settings == sample_settings


@patch('requests.post')
def test_set_settings_remote_tool(mock_post):
    """
    Test updating settings on a remote tool's settings endpoint.
    Mocks the requests.post call to return a sample successful response.
    """
    # Define a sample response for successful settings update
    sample_response = {
        "status": "success",
        "message": "Settings updated."
    }
    # Mock the POST request to the tool's settings endpoint
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = sample_response
    mock_post.return_value = mock_response
    # Tool reference and settings to be updated
    tool_reference = "http://example.com"
    settings = {
        "setting1": "new_value1",
        "setting2": "new_value2"
    }
    # Create an instance of ToolManager with required config
    tool_manager = ToolDiscovery()
    # Invoke the set_settings method
    result = tool_manager.set_settings(tool_reference, settings)
    # Assertions to validate the response
    mock_post.assert_called_once_with(
        f"{tool_reference}/settings",
        json=settings,
        timeout=10,
        verify=True
    )
    assert result == sample_response


@patch('requests.post')
def test_set_settings_remote_tool_error(mock_post):
    """
    Test handling of errors when updating settings on a remote tool's settings endpoint.
    Mocks the requests.post call to simulate an HTTP error response.
    """
    # Mock the POST request to return an HTTP error
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.raise_for_status.side_effect = HTTPError("Error updating settings")
    mock_post.return_value = mock_response
    # Tool reference and settings to be updated
    tool_reference = "http://example.com"
    settings = {
        "setting1": "new_value1",
        "setting2": "new_value2"
    }
    # Create an instance of ToolManager with required config
    tool_manager = ToolDiscovery()
    # Attempt to invoke set_settings and expect an HTTPError
    with pytest.raises(HTTPError, match="Error updating settings"):
        tool_manager.set_settings(tool_reference, settings)
    # Assertions to validate that the POST request was made as expected
    mock_post.assert_called_once_with(
        f"{tool_reference}/settings",
        json=settings,
        timeout=10,
        verify=True
    )


def test_get_settings_local_tool(tool_discovery):  # pylint: disable=W0621
    """
    Test getting settings from a local tool path.
    Verifies that a ValueError is raised when a local path is provided.
    """
    # Use a local file path as the tool_reference
    tool_reference = '/local/path/to/tool'
    # Invoke the get_settings method with a local path and expect ValueError
    with pytest.raises(ValueError, match="Local tool not supported"):
        tool_discovery.get_settings(tool_reference)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
