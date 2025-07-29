#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for the TemplateEngine class that handles Jinja2 templates.
"""

import os
import pytest
from jinja2 import TemplateNotFound
from src.lib.services.core.template_engine import TemplateEngine


@pytest.fixture
def template_engine():
    """
    Fixture for TemplateEngine instance.
    """
    return TemplateEngine()

def test_render_template_string_success(template_engine):  # pylint: disable=W0621
    """
    Test rendering from a template string with parameters.
    """
    template_string = "Hello, {{ name }}!"
    params = {"name": "Alice"}
    result = template_engine.render(template_string, **params)
    assert result == "Hello, Alice!"


def test_render_template_string_missing_param(template_engine):  # pylint: disable=W0621
    """
    Test rendering from a template string with a missing parameter.
    """
    template_string = "Hello, {{ name }}!"
    params = {}  # Missing 'name' parameter
    result = template_engine.render(template_string, **params)
    assert result == "Hello, !"


def test_load_template_file_success(template_engine, tmp_path):  # pylint: disable=W0621
    """
    Test loading and rendering a template from a file.
    """
    env_path = tmp_path / "templates"
    env_path.mkdir()
    template_file = env_path / "greeting_template.txt"
    template_file.write_text("Hello, {{ name }}!", encoding="utf-8")
    result = template_engine.load(str(env_path), "greeting_template.txt", name="Alice")
    assert result == "Hello, Alice!"


def test_load_template_file_not_found(template_engine, tmp_path):  # pylint: disable=W0621
    """
    Test loading a template file that does not exist.
    """
    env_path = tmp_path / "templates"
    env_path.mkdir()
    with pytest.raises(TemplateNotFound):
        template_engine.load(str(env_path), "nonexistent_template.txt", name="Alice")


def test_save_template_file_success(template_engine, tmp_path):  # pylint: disable=W0621
    """
    Test saving content to a file.
    """
    env_path = tmp_path / "output"
    env_path.mkdir()
    file_name = "saved_template.txt"
    content = "Hello, Alice!"
    template_engine.save(str(env_path), file_name, content)
    saved_file = env_path / file_name
    assert saved_file.read_text(encoding="utf-8") == content


def test_save_template_file_failure(template_engine):  # pylint: disable=W0621
    """
    Test the save method for a failure scenario, such as an invalid path.
    """
    env_path = "/invalid/path"
    file_name = "saved_template.txt"
    content = "Hello, Alice!"
    with pytest.raises(OSError):
        template_engine.save(env_path, file_name, content)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
