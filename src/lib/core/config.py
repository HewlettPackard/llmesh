#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module defines the Config class, which is responsible for handling the configuration
settings of an application. 

The Config class loads settings from a specified YAML file,
provides a mechanism for placeholder variable substitution within these settings, and
ensures that these settings are easily accessible throughout an application.
"""

import os
from os.path import join, dirname
import inspect
from dotenv import load_dotenv
import yaml
from src.lib.core.template_engine import TemplateEngine
from src.lib.core.log import Logger


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
logger = Logger().get_logger()


class Config:
    """
    A class used to represent and manage configuration settings for an application.
    """

    def __init__(
            self,
            config_file: str = "",
            setup_parameters: dict = None,
            sensitive_keys: tuple = ("api_key", "secret", "password"),
            replace_placeholders: bool = True):
        """
        Initialize the Config class.

        :param config_file: Path to the YAML configuration file.
        :param setup_parameters: Optional setup parameters for tool configuration.
        :param replace_placeholders: Whether to replace placeholders in the configuration file.
        """
        self.config_file = config_file
        self.setup_parameters = setup_parameters
        self.replace_placeholders = replace_placeholders
        self.sentitive_keys = sensitive_keys
        self.prompts = None
        self.settings = self.load_yaml()

    def load_yaml(self) -> dict:
        """
        Load the configuration file and return the settings dictionary.

        :return: Dictionary containing configuration settings.
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                raw_content = file.read()
                file_data = yaml.safe_load(raw_content)
                self.prompts = file_data.get("prompts", {})
            settings = self._replace_placeholders_in_data(file_data)
            if settings:
                settings["_file_path"] = self.config_file
                settings["_raw_file"] = raw_content
                settings["_sentitive_keys"] = self.sentitive_keys
            return settings
        except FileNotFoundError:
            logger.error("YAML configuration file not found: %s", self.config_file)
        except yaml.YAMLError as e:
            logger.error("Error parsing the YAML file: %s", e)
        except Exception as e:  # pylint: disable=W0718
            logger.error("An unexpected error occurred: %s", e)
        return {}

    def _replace_placeholders_in_data(self, data: any) -> any:
        """
        Recursively replace placeholders with environment variable values in a nested structure.

        :param data: The data structure containing placeholders.
        :return: Data with placeholders replaced.
        """
        if self.replace_placeholders:
            if isinstance(data, dict):
                return {
                    key: self._replace_placeholders_in_data(value) for key, value in data.items()
                }
            if isinstance(data, list):
                return [self._replace_placeholders_in_data(item) for item in data]
            if isinstance(data, str):
                return self._replace_placeholder(data)
        return data

    def _replace_placeholder(self, value: str) -> str:
        """
        Replace a single placeholder with its corresponding value.

        :param value: The string containing the placeholder.
        :return: The string with the placeholder replaced.
        """
        if value.startswith("$ENV{") and value.endswith("}"):
            env_var = value[5:-1]
            return os.getenv(env_var, value)
        if value.startswith("$PROMPT{") and value.endswith("}"):
            prompt_name = value[8:-1]
            return self._resolve_prompt(prompt_name)
        if value.startswith("$FUNCTION{") and value.endswith("}"):
            function_name = value[10:-1]
            return function_name
        if value.startswith("$TOOL{") and value.endswith("}"):
            tool_name = value[6:-1]
            return self._resolve_tool(tool_name)
        return value

    def _resolve_prompt(self, prompt_name: str) -> str:
        """
        Resolve a prompt placeholder by rendering it.

        :param prompt_name: The name of the prompt to render.
        :return: The rendered prompt content.
        """
        template = TemplateEngine()
        content = template.load(
            self.prompts["environment"],
            self.prompts["templates"][prompt_name])
        return content

    def _resolve_tool(self, tool_name: str) -> any:
        """
        Resolve a tool placeholder by finding and instantiating the corresponding tool.

        :param tool_name: The name of the tool to instantiate.
        :return: The instantiated tool object or None if not found.
        """
        if self._validate_tool_setup():
            base_tool_classes = self._find_base_tool_classes(
                self.setup_parameters["tool"]["module"],
                self.setup_parameters["tool"]["base_class"],
            )
            return self._instantiate_tool_by_name(base_tool_classes, tool_name)
        return None

    def _validate_tool_setup(self) -> bool:
        """
        Validate that the tool setup parameters are correctly provided.

        :return: True if setup parameters are valid, False otherwise.
        """
        if self.setup_parameters:
            tool_params = self.setup_parameters.get("tool", {})
            required_keys = {"module", "base_class"}
            return required_keys <= tool_params.keys()
        return False

    def _find_base_tool_classes(self, module, base_class) -> list:
        """
        Find all subclasses of the specified base class within a module.

        :param module: The module to search for tool classes.
        :param base_class: The base class to find subclasses of.
        :return: A list of tuples containing the name and class of each tool found.
        """
        return [
            (name, obj) for name, obj in inspect.getmembers(module, inspect.isclass)
            if issubclass(obj, base_class) and obj is not base_class
        ]

    def _instantiate_tool_by_name(self, tool_classes: list, class_name: str) -> any:
        """
        Instantiate a tool class by its name.

        :param tool_classes: A list of tool classes to search through.
        :param class_name: The name of the class to instantiate.
        :return: An instance of the class if found, or None if not found.
        """
        for name, obj in tool_classes:
            if name == class_name:
                return obj()
        return None


    def save_yaml(self, settings: dict, output_file: str = None) -> None:
        """
        Save the provided settings to a YAML file.

        :param settings: The settings dictionary to save.
        :param output_file: The file to save the settings to. Defaults to the config file path.
        """
        output_file = output_file or self.config_file
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                yaml.safe_dump(settings, file, allow_unicode=True)
            logger.info("YAML configuration saved to: %s", output_file)
        except Exception as e:  # pylint: disable=W0718
            logger.error("An error occurred while saving the YAML file: %s", e)


    def get_settings(self) -> dict:
        """
        Retrieve the current configuration settings.

        :return: The dictionary of configuration settings.
        """
        return self.settings
