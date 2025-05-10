#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to handle prompt from template files

This script is designed to generate a prompt from a file using 
Jinja2 and some input parameters.
"""

from jinja2 import Template, Environment, FileSystemLoader
from src.lib.core.log import Logger
from src.lib.services.chat.prompt_renders.base import BasePromptRender


logger = Logger().get_logger()


class JinjaTemplatePromptRender(BasePromptRender):
    """
    Prompt Render class to manage prompts.
    """

    def __init__(self, config: dict) -> None:
        """
        Initialize the file render with the given configuration.

        :param config: Configuration dictionary for the file render.
        """
        self.config = JinjaTemplatePromptRender.Config(**config)
        self.result = JinjaTemplatePromptRender.Result()

    def render(self, template_string: str, **params: dict) -> 'JinjaTemplatePromptRender.Result':
        """
        Generates a tool prompt from a template etring passed as input,
        utilizing additional parameters for customization.

        :param template: The template string.
        :param params: Additional parameters for rendering the template.
        :return: Result object containing the status and generated content.
        """
        try:
            template = Template(template_string)
            self.result.status = "success"
            self.result.content = template.render(params)
            logger.debug(f"Prompt generated from string with params {params}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while rendering the template: {e}"
            logger.error(self.result.error_message)
        return self.result

    def load(self, prompt_name: str, **params: dict) -> 'JinjaTemplatePromptRender.Result':
        """
        Generates a tool prompt from a template file located in a specified environment,
        utilizing additional parameters for customization.

        :param prompt_name: The name of the prompt template to load.
        :param params: Additional parameters for rendering the template.
        :return: Result object containing the status and generated content.
        """
        try:
            env_path = self.config.environment
            file_path = self.config.templates[prompt_name]
            environment = Environment(loader=FileSystemLoader(env_path))
            template = environment.get_template(file_path)
            self.result.status = "success"
            self.result.content = template.render(params)
            logger.debug(f"Prompt generated from {env_path}/{file_path} with params {params}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while loading the template: {e}"
            logger.error(self.result.error_message)
        return self.result

    def save(self, prompt_name: str, content: str) -> 'JinjaTemplatePromptRender.Result':
        """
        Save the provided prompt content to a file.

        :param prompt_name: The name of the prompt template to save.
        :param content: The content to save.
        :return: Result object containing the status of the save operation.
        """
        output_file = f"{self.config.environment}/{self.config.templates[prompt_name]}"
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(content)
            self.result.status = "success"
            logger.info(f"Prompt content saved to: {output_file}")
        except OSError as e:
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while saving the prompt file: {e}"
            logger.error(self.result.error_message)
        return self.result
