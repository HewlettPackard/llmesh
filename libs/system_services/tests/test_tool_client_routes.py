#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The tests ensure that the AthonTool class properly initializes with valid routes. 
These tests help in verifying that the configuration for the tool are enforced correctly, 
which is crucial for ensuring stability and predictable behavior in production environments.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from flask import jsonify
from libs.core.template_engine import TemplateEngine
from libs.system_services.tool_client import AthonTool


@pytest.fixture
def app():
    """Fixture to set up the Flask application instance for testing."""
    config = {
        'tool': {
            'name': 'TestTool',
            'function': 'lambda x: x',
            'description': 'A simple test tool',
            'arguments': [{'name': 'x', 'type': 'int', 'description': 'A number'}]
        },
        "_file_path": "/path/to/config",
        "_sentitive_keys": ["api_key", "secret", "password"],
        "function": {"api_key": "api_key_value"},
        "prompts": {"environment": "/path/to/prompts"}
    }
    logger = MagicMock()
    tool = AthonTool(config, logger)
    return tool.run_app(test=True)

@pytest.fixture
def client(app):  # pylint: disable=W0621
    """Flask test client for making requests."""
    return app.test_client()

def test_get_manifest(client):  # pylint: disable=W0621
    """
    Test the /manifest endpoint to retrieve the tool's manifest.
    """
    with patch.object(
        AthonTool,
        'get_manifest',
        return_value={'name': 'TestTool', 'description': 'A test tool'}):
        response = client.get('/manifest')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'TestTool'
        assert data['description'] == 'A test tool'


def test_get_manifest_failure(client):  # pylint: disable=W0621
    """
    Test the /manifest endpoint to handle a failure in generating the manifest.
    """
    with patch.object(
        AthonTool,
        'get_manifest', 
        side_effect=Exception("Manifest generation error")):
        response = client.get('/manifest')
        assert response.status_code == 500
        assert "Manifest generation error" in response.get_data(as_text=True)


def test_tool_invocation_get_success(client, app):  # pylint: disable=W0621
    """
    Test the /tool endpoint with GET method for successful invocation.
    """
    with app.app_context():
        with patch.object(AthonTool, 'invoke', return_value=jsonify({"result": "success"})):
            response = client.get('/tool', query_string={'x': 10})
            assert response.status_code == 200
            data = response.get_json()
            assert data['result'] == 'success'


def test_tool_invocation_post_success(client, app):  # pylint: disable=W0621
    """
    Test the /tool endpoint with POST method for successful invocation.
    """
    with app.app_context():
        with patch.object(AthonTool, 'invoke', return_value=jsonify({"result": "success"})):
            response = client.post('/tool', json={'x': 10})
            assert response.status_code == 200
            data = response.get_json()
            assert data['result'] == 'success'


def test_tool_invocation_missing_params(client):  # pylint: disable=W0621
    """
    Test the /tool endpoint to handle missing parameters, expecting a 400 error.
    """
    response = client.get('/tool')  # Missing 'x' parameter
    assert response.status_code == 400
    data = response.get_json()
    assert "Missing parameters: ['x']" in data['error']


def test_get_settings(client):  # pylint: disable=W0621
    """
    Test the /settings endpoint to retrieve the current settings.
    """
    response = client.get('/settings')
    assert response.status_code == 200
    data = response.get_json()
    assert "_file_path" in data
    assert "prompts" in data
    assert data["_file_path"] == "/path/to/config"
    assert data["_sentitive_keys"] == ["api_key", "secret", "password"]
    assert data["prompts"]["environment"] == "/path/to/prompts"
    assert data["tool"]["name"] == "TestTool"
    assert data["function"]["api_key"] == "***MASKED***"


def test_set_settings(client):  # pylint: disable=W0621
    """
    Test the /settings endpoint to update the current settings.
    """
    # Define new settings to update
    new_settings = {
        "function": {"api_key": "new_api_key"},
        "tool": {"name": "UpdatedTool"}
    }
    # Send a POST request with new settings
    response = client.post('/settings', json=new_settings)
    assert response.status_code == 200
    # Check that the response indicates success
    data = response.get_json()
    assert data["status"] == "success"
    assert data["message"] == "Settings updated."
    # Verify that the settings were updated
    response = client.get('/settings')
    assert response.status_code == 200
    updated_data = response.get_json()
    assert updated_data["tool"]["name"] == "UpdatedTool"
    assert updated_data["function"]["api_key"] == "***MASKED***"


def test_save_file_success(client):  # pylint: disable=W0621
    """
    Test the /files endpoint to save a CONFIG file successfully.
    """
    with patch.object(TemplateEngine, 'save', return_value=True):
        response = client.post('/files', json={
            "type": "CONFIG",
            "file_name": "config.txt",
            "file_content": "Sample configuration content"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "saved successfully" in data["message"]


def test_save_file_invalid_type(client):  # pylint: disable=W0621
    """
    Test the /files endpoint with an invalid file type, expecting a 400 error.
    """
    response = client.post('/files', json={
        "type": "UNSUPPORTED_TYPE",
        "file_name": "invalid.txt",
        "file_content": "This should fail"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Invalid file type specified"


def test_save_file_failure(client):  # pylint: disable=W0621
    """
    Test the /files endpoint to handle a file save failure (e.g., invalid path).
    """
    with patch.object(TemplateEngine, 'save', side_effect=OSError("File save error")):
        response = client.post('/files', json={
            "type": "CONFIG",
            "file_name": "config.txt",
            "file_content": "Sample content"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "failure"
        assert "File save error" in data["error_message"]


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
