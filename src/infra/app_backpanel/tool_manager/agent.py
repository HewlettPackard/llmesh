#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for validating agent tools based on provided entries and settings and
for handling its route endpoints
"""

import os
import copy
from packaging.version import Version, InvalidVersion
from langchain.schema import HumanMessage, SystemMessage
from athon.chat import ChatModel, PromptRender
from athon.system import Config, Logger, ToolDiscovery
from src.infra.app_backpanel.tool_manager.base import ToolManager


# Parse command-line arguments and start the application
PATH = 'src/infra/app_backpanel/'
CONFIG = Config(PATH+'config.yaml', replace_placeholders=False).get_settings()
# Create Logger
logger = Logger().configure(CONFIG['logger']).get_logger()


class AgentTool(ToolManager):
    "Agent Tool Manager class"

    def validate(self, index, tool_settings):
        """
        Validates a agent tool by performing a series of validation steps.

        Parameters:
            index (int): The index of the tool in the list.
            tool_settings (dict): The tool settings including configuration details.

        Returns:
            dict or None: A dictionary of tool information if validation is successful,
                None otherwise.
        """
        validation_steps = [
            self._validate_agent_tool_name,
            self._validate_agent_tool_version,
            self._validate_agent_tool_function_data,
        ]
        for step in validation_steps:
            error = step(
               index,
               tool_settings
            )
            if error:
                logger.error(error)
                return None
        return self._get_agent_tool_info(index, tool_settings)

    def _validate_agent_tool_name(self, index, tool_settings):
        tool_name = self.tool_entry.get('name')
        settings_name = tool_settings.get('tool', {}).get('name')
        if tool_name != settings_name:
            return f"Tool name mismatch at index {index}: '{tool_name}' != '{settings_name}'"
        return None

    def _validate_agent_tool_version(self, index, tool_settings):
        min_version = self.tool_entry.get('version', {}).get('min_version')
        max_version = self.tool_entry.get('version', {}).get('max_version')
        tool_version = tool_settings.get('version')
        if not all([min_version, max_version, tool_version]):
            return f"Missing version information for tool at index {index}."
        try:
            if not Version(min_version) <= Version(tool_version) < Version(max_version):
                return f"Unsupported tool version '{tool_version}' at index {index}."
        except InvalidVersion as e:
            return f"Invalid version format in tool entry at index {index}: {e}"
        return None

    def _validate_agent_tool_function_data(self, index, tool_settings):
        function_data = tool_settings.get('function')
        if not function_data:
            return f"Missing 'function' for tool {self.tool_entry.get('name')} at idx {index}."
        multi_agents_dat = function_data.get('multi_agents')
        if not isinstance(multi_agents_dat, dict):
            return f"Invalid 'multi_agents' type at index {index}. Expected a dictionary."
        llm_data = multi_agents_dat.get('llm')
        if not isinstance(llm_data, dict):
            return f"Invalid 'llm' type at index {index}. Expected a dictionary."
        return None

    def _get_agent_tool_info(self, index, tool_settings):
        logger.info(
            f"Tool '{self.tool_entry['name']}' at index {index} validated successfully."
        )
        return {
            'id': index,
            'type': self.tool_entry['type'],
            'name': self.tool_entry['name'],
            'base_url': self.tool_entry['base_url'],
            'settings': tool_settings,
            'options': self.tool_entry,
        }

    def get_settings(self):
        """
        Retrieves the 'settings' dictionary from a given tool entry if it exists.

        Returns:
            dict or None: The 'settings' dictionary from the tool entry if available, or None.
        """
        if self.tool_info:
            return self.tool_info
        return None

    def set_settings(self, tool_settings, default_flag):
        """
        Saves the tool settings.

        Parameters:
            tool_settings (dict): The tool settings including configuration details.
            default_flag (bool): Default flag

        Returns:
            Any or None: The result of the validation, or None if validation fails.
        """
        new_tool_info = copy.deepcopy(self.tool_info)
        if default_flag:
            default_settings = self._get_default_settings()
            new_tool_info['settings']['function']['multi_agents']['llm'] = (
                default_settings['function']['multi_agents']['llm'])
            new_tool_info['settings']['function']['multi_agents']['plan_type'] = (
                default_settings['function']['multi_agents']['plan_type'])
        return new_tool_info

    def _get_default_settings(self):
        path = self.tool_info['options']['default']['path']
        file_name = self.tool_info['options']['default']['files']['config']
        return Config(path+file_name, replace_placeholders=False).get_settings()

    def improve_prompt(self, system_prompt):
        """
        Improve the system prompts using LLM.

        Parameters:
            system_prompt (str): Actual system prompt

        Returns:
            String: Updated system prompt.
        """
        prompts = [
            SystemMessage(content = self._get_prompt("system_prompt")),
            HumanMessage(content = f"Imnprove: '''{system_prompt}'''")
        ]
        completion = self._invoke_llm(prompts)
        logger.debug(f"COMPLETION:\n{completion}")
        return completion

    def _get_prompt(self, template):
        prompt = PromptRender.create(CONFIG['prompts'])
        result = prompt.load(template)
        return result.content

    def _invoke_llm(self, messages):
        llm_config = self._get_llm_config()
        chat = ChatModel.create(llm_config)
        result = chat.invoke(messages)
        return result.content

    def _get_llm_config(self):
        llm_config = CONFIG['function']['llm']
        api_key = llm_config['api_key']
        # Replace unresolved environment variable
        if api_key.startswith("$ENV{") and api_key.endswith("}"):
            env_var = api_key[5:-1]
            llm_config['api_key'] =  os.getenv(env_var, api_key)
        return llm_config

    def apply_settings(self, tool_settings):
        """
        Sets the tool settings.

        Parameters:
            tool_settings (dict): The tool settings including configuration details.
            default_flag (bool): Default flag

        Returns:
            String: Result of operation
        """
        config = {
            "function/multi_agents/llm": self._get_llm_option(tool_settings["llm"]),
            "function/multi_agents/plan_type": tool_settings["plan_type"]
        }
        base_url = self.tool_info.get('base_url')
        tool_discovery = ToolDiscovery(CONFIG["function"]["discovery"])
        return tool_discovery.set_settings(base_url, config)

    def _get_llm_option(self, llm_name):
        for llm in self.tool_info["options"]["llms"]:
            if llm.get("label") == llm_name:
                return llm.get("settings")
        return None
