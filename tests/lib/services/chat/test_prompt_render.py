#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This test module verifies the functionality of the PromptRender factory class 
and the JinjaTemplatePromptRender class that use jinja2 to create prompts 
to be used by LLM from template files and parameters.
"""

import os
import pytest
from src.lib.services.chat.prompt_render import PromptRender
from src.lib.services.chat.prompt_renders.jinja.template import JinjaTemplatePromptRender


@pytest.fixture
def jinja_template_config():
    """
    Mockup configuration for JinjaTemplatePromptRender
    """
    return {
        "type": "JinjaTemplate",
        "environment": "path/to/config",
        "templates": {
            "greeting": "greeting_template.txt"
        }
    }


def test_prompt_render_create_jinja_template(jinja_template_config):  # pylint: disable=W0621
    """
    Test the PromptRender factory to ensure it creates a JinjaTemplatePromptRender instance
    """
    prompt_render = PromptRender.create(jinja_template_config)
    assert isinstance(prompt_render, JinjaTemplatePromptRender)


def test_prompt_render_create_invalid_type():
    """
    Test the PromptRender factory to ensure it raises a ValueError for unsupported types
    """
    config = {
        "type": "UnsupportedType"
    }
    with pytest.raises(ValueError, match="Unsupported prompt file render type: UnsupportedType"):
        PromptRender.create(config)


@pytest.fixture
def jinja_template_prompt_render(jinja_template_config):  # pylint: disable=W0621
    """
    Fixture for JinjaTemplatePromptRender instance
    """
    return JinjaTemplatePromptRender(jinja_template_config)


def test_render_template_string_success(jinja_template_prompt_render):  # pylint: disable=W0621
    """
    Test the render method for successful prompt generation from a template string
    """
    template_string = "Hello, {{ name }}!"
    params = {"name": "John"}
    result = jinja_template_prompt_render.render(template_string, **params)
    assert result.status == "success"
    assert result.content == "Hello, John!"


def test_render_template_string_failure(jinja_template_prompt_render):  # pylint: disable=W0621
    """
    Test the render method for failure scenario
    """
    template_string = "Hello, {{ name }"
    params = {"name": "John"}
    result = jinja_template_prompt_render.render(template_string, **params)
    assert result.status == "failure"
    assert result.error_message is not None


def test_load_template_file_success(jinja_template_prompt_render, tmp_path):  # pylint: disable=W0621
    """
    Test the load method for successful prompt generation from a template file
    """
    env_path = tmp_path / "path/to/config"
    env_path.mkdir(parents=True)
    template_file = env_path / "greeting_template.txt"
    template_file.write_text("Hello, {{ name }}!", encoding="utf-8")
    params = {"name": "John"}
    jinja_template_prompt_render.config.environment = str(env_path)
    result = jinja_template_prompt_render.load("greeting", **params)
    assert result.status == "success"
    assert result.content == "Hello, John!"


def test_load_template_file_failure(jinja_template_prompt_render):  # pylint: disable=W0621
    """
    Test the load method for failure scenario
    """
    params = {"name": "John"}
    result = jinja_template_prompt_render.load("nonexistent_template", **params)
    assert result.status == "failure"
    assert result.error_message is not None


def test_save_template_file_success(jinja_template_prompt_render, tmp_path):  # pylint: disable=W0621
    """
    Test the save method for successful prompt saving to a file
    """
    env_path = tmp_path / "path/to/config"
    env_path.mkdir(parents=True)
    jinja_template_prompt_render.config.environment = str(env_path)
    jinja_template_prompt_render.config.templates["greeting"] = "saved_template.txt"
    content = "Hello, John!"
    result = jinja_template_prompt_render.save("greeting", content)
    assert result.status == "success"
    saved_file = env_path / "saved_template.txt"
    assert saved_file.read_text(encoding="utf-8") == content


def test_save_template_file_failure(jinja_template_prompt_render):  # pylint: disable=W0621
    """
    Test the save method for failure scenario
    """
    jinja_template_prompt_render.config.environment = "/invalid/path"
    jinja_template_prompt_render.config.templates["greeting"] = "saved_template.txt"
    content = "Hello, John!"
    result = jinja_template_prompt_render.save("greeting", content)
    assert result.status == "failure"
    assert result.error_message is not None


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
