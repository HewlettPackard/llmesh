#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to handle prompt from template files

This script is designed to generate a prompt from a file using 
Jinja2 and some input parameters.
"""

from __future__ import annotations
from typing import Dict, Optional
from pydantic import Field
from jinja2 import Template, Environment, FileSystemLoader
from src.lib.core.log import Logger
from src.lib.services.chat.prompt_renders.base import BasePromptRender
from src.lib.services.chat.prompt_renders.error_handler import prompt_error_handler


logger = Logger().get_logger()


class JinjaTemplatePromptRender(BasePromptRender):
    """
    Prompt Render class to manage prompts.
    """

    class Config(BasePromptRender.Config):
        """
        Configuration for the Prompt Render class.
        """
        environment: Optional[str] = Field(
            None,
            description="Path to the environment configuration folder"
        )
        templates: Optional[Dict[str, str]] = Field(
            None,
            description="Dictionary of templates with key-value pairs representing template details"
        )

    def __init__(self, config: dict) -> None:
        """
        Initialize the file render with the given configuration.

        :param config: Configuration dictionary for the file render.
        """
        self.config = JinjaTemplatePromptRender.Config(**config)
        self.result = JinjaTemplatePromptRender.Result()

    @prompt_error_handler("An error occurred while rendering the template")
    def render(self, template_string: str, **params: dict) -> JinjaTemplatePromptRender.Result:
        """
        Generates a tool prompt from a template etring passed as input,
        utilizing additional parameters for customization.

        :param template: The template string.
        :param params: Additional parameters for rendering the template.
        :return: Result object containing the status and generated content.
        """
        template = Template(template_string)
        self.result.status = "success"
        self.result.content = template.render(params)
        logger.debug(f"Prompt generated from string with params {params}")
        return self.result

    @prompt_error_handler("An error occurred while loading the template")
    def load(self, prompt_name: str, **params: dict) -> JinjaTemplatePromptRender.Result:
        """
        Generates a tool prompt from a template file located in a specified environment,
        utilizing additional parameters for customization.

        :param prompt_name: The name of the prompt template to load.
        :param params: Additional parameters for rendering the template.
        :return: Result object containing the status and generated content.
        """
        env_path = self.config.environment
        file_path = self.config.templates[prompt_name]
        environment = Environment(loader=FileSystemLoader(env_path))
        template = environment.get_template(file_path)
        self.result.status = "success"
        self.result.content = template.render(params)
        logger.debug(f"Prompt generated from {env_path}/{file_path} with params {params}")
        return self.result

    @prompt_error_handler("An error occurred while saving the template")
    def save(self, prompt_name: str, content: str) -> JinjaTemplatePromptRender.Result:
        """
        Save the provided prompt content to a file.

        :param prompt_name: The name of the prompt template to save.
        :param content: The content to save.
        :return: Result object containing the status of the save operation.
        """
        output_file = f"{self.config.environment}/{self.config.templates[prompt_name]}"
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        self.result.status = "success"
        logger.info(f"Prompt content saved to: {output_file}")
        return self.result
