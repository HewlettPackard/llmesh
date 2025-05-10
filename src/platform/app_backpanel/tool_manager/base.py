#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Tool Manager

Placeholder class that has to be overwritten
"""

import abc


class ToolManager(abc.ABC):  # pylint: disable=R0903
    "Base Tool Manager class"

    def __init__(self, tool_info, partial):
        self.partial = partial
        if self.partial:
            self.tool_entry = tool_info
            self.tool_info = None
        else:
            self.tool_entry = None
            self.tool_info = tool_info

    def validate(self, index, tool_settings):
        """
        Validates the tool settings.

        Parameters:
            index (int): The index of the tool in the list.
            tool_settings (dict): The tool settings including configuration details.

        Returns:
            Any or None: The result of the validation, or None if validation fails.
        """
        raise NotImplementedError("Subclasses must implement the 'validate' method.")

    def get_settings(self):
        """
        Retrieves the tool settings.

        Returns:
            dict or None: The settings dictionary if available, otherwise None.
        """
        raise NotImplementedError("Subclasses must implement the 'get_settings' method.")

    def set_settings(self, tool_settings, default_flag):
        """
        Sets the tool settings.

        Parameters:
            tool_settings (dict): The tool settings including configuration details.
            default_flag (bool): Default flag

        Returns:
            Any or None: Updated settings, or None if fails.
        """
        raise NotImplementedError("Subclasses must implement the 'set_settings' method.")

    def improve_prompt(self, system_prompt):
        """
        Improve the system prompts using LLM.

        Parameters:
            system_prompt (str): Actual system prompt

        Returns:
            String: Updated system prompt.
        """
        raise NotImplementedError("Subclasses must implement the 'improve_prompt' method.")

    def apply_settings(self, tool_settings):
        """
        Sets the tool settings.

        Parameters:
            tool_settings (dict): The tool settings including configuration details.
            default_flag (bool): Default flag

        Returns:
            String: Result of operation
        """
        raise NotImplementedError("Subclasses must implement the 'apply_settings' method.")
