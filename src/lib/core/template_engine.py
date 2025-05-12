#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class to handle template files

This script is designed to generate a prompt from a file using 
Jinja2 and some input parameters.
"""

from jinja2 import Template, Environment, FileSystemLoader
from src.lib.core.log import Logger


logger = Logger().get_logger()


class TemplateEngine:
    """
    Template Engine class to manage templates.
    """

    def render(self, template_string: str, **params: dict) -> str:
        """
        Generates a tool prompt from a template etring passed as input,
        utilizing additional parameters for customization.

        :param template: The template string.
        :param params: Additional parameters for rendering the template.
        :return: Generated content.
        """
        template = Template(template_string)
        logger.debug(f"Template generated from string with params {params}")
        return template.render(params)

    def load(self, env_path: str, file_name: str, **params: dict) -> str:
        """
        Generates a tool prompt from a template file located in a specified environment,
        utilizing additional parameters for customization.

        :param env_path: Environment path.
        :param file_name: The name of the file template to load.
        :param params: Additional parameters for rendering the template.
        :return: Generated content.
        """
        environment = Environment(loader=FileSystemLoader(env_path))
        template = environment.get_template(file_name)
        logger.debug(f"Template generated from {env_path}/{file_name} with params {params}")
        return template.render(params)

    def save(self, env_path: str, file_name: str, content: str):
        """
        Save the provided prompt content to a file.

        :param env_path: Environment path.
        :param file_name: The name of the file template to load.
        :param content: The content to save.
        """
        output_file = f"{env_path}/{file_name}"
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"Template saved to: {output_file}")
