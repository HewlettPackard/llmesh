#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for the Config class which handles reading and processing 
configuration settings from a YAML file.
"""

import os
from unittest.mock import mock_open, patch
import yaml
import pytest
from self_serve_platform.system.config import Config


# Example YAML content with various placeholders
YAML_CONTENT_PLACEHOLDERS = """
database:
  host: $ENV{DB_HOST}
  port: 5432
"""
# Mocked environment variables
os.environ['DB_HOST'] = 'localhost'


def test_load_yaml_success():
    """
    Test loading a valid YAML configuration file and check environment variable substitution.
    """
    with patch("builtins.open", mock_open(read_data=YAML_CONTENT_PLACEHOLDERS)):
        with patch("os.path.exists", return_value=True):
            config = Config("dummy_path.yaml")
            assert config.settings['database']['host'] == 'localhost'
            assert config.settings['database']['port'] == 5432
            assert '_file_path' in config.settings
            assert config.settings['_file_path'] == 'dummy_path.yaml'


def test_load_yaml_file_not_found():
    """
    Test the response of the Config class when the specified YAML file does not exist.
    """
    with patch("builtins.open", side_effect=FileNotFoundError()):
        config = Config("nonexistent.yaml")
        assert config.settings == {}


def test_load_yaml_parse_error():
    """
    Test the behavior when the YAML file is malformed.
    """
    with patch("builtins.open", mock_open(read_data=":")):  # Malformed YAML
        with patch("yaml.safe_load", side_effect=yaml.YAMLError("error")):
            config = Config("invalid.yaml")
            assert config.settings == {}


def test_get_settings():
    """
    Test the retrieval of settings after successful loading.
    """
    with patch("builtins.open", mock_open(read_data=YAML_CONTENT_PLACEHOLDERS)):
        config = Config("dummy_path.yaml")
        assert config.get_settings() == config.settings


@pytest.mark.parametrize("input,expected", [
    ("$ENV{DB_HOST}", "localhost"),
    ("static_value", "static_value"),
    ("$ENV{NONEXISTENT_VAR}", "$ENV{NONEXISTENT_VAR}"),
    ("$PROMPT{USERNAME}", "mocked_username"),
    ("$FUNCTION{process_data}", "process_data"),
    ("$TOOL{ExampleTool}", None)
])

def test_replace_placeholder_variables(input, expected):  # pylint: disable=W0622
    """
    Test the _replace_placeholder_variables private method to ensure it replaces placeholders 
    correctly or returns the original string if the variable is not set.
    """
    with patch.object(Config, '_resolve_prompt', return_value="mocked_username"):
        with patch.object(Config, '_resolve_tool', return_value=None):
            config = Config()
            result = config._replace_placeholders_in_data(input)  # pylint: disable=W0212
            assert result == expected


def test_save_yaml():
    """
    Test the save_yaml method to ensure the settings are saved to a YAML file correctly.
    """
    settings = {
        'database': {
            'host': 'localhost',
            'port': 5432
        }
    }
    with patch("builtins.open", mock_open()) as mocked_file:
        config = Config("dummy_path.yaml")
        config.save_yaml(settings)
        # Combine all write calls into a single string
        written_data = ''.join(call.args[0] for call in mocked_file().write.call_args_list)
        # Check if the final written data matches the expected YAML content
        assert yaml.safe_load(written_data) == settings

def test_load_yaml_preserves_raw_text():
    """
    Test that '_raw_file' in the settings contains the exact original YAML text,
    while placeholders in 'settings' are resolved.
    """
    raw_data = "database:\nhost: $ENV{DB_HOST}\nport: 5432"
    # Patch the file open so that reading it returns our raw_data
    with patch("builtins.open", mock_open(read_data=raw_data)):
        with patch("os.path.exists", return_value=True):
            config = Config("dummy_path.yaml")
            # Check that the raw YAML is preserved exactly
            assert config.settings["_raw_file"] == raw_data


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
