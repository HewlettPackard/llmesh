#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for validating rag tools based on provided entries and settings and
for handling its route endpoints
"""

import os
import copy
from packaging.version import Version, InvalidVersion
from langchain.schema import HumanMessage, SystemMessage
from libs.chat.model import ChatModel
from libs.core.config import Config
from libs.core.log import Logger
from libs.system_services.tool_server import ToolDiscovery
from libs.chat.prompt_render import PromptRender
from libs.rag.data_extractor import DataExtractor
from libs.rag.data_transformer import DataTransformer
from libs.rag.data_storage import DataStorage
from libs.rag.data_loader import DataLoader
from src.platform.app_backpanel.tool_manager.base import ToolManager



# Parse command-line arguments and start the application
PATH = 'src/platform/app_backpanel/'
CONFIG = Config(PATH+'config.yaml', replace_placeholders=False).get_settings()
# Create Logger
logger = Logger().configure(CONFIG['logger']).get_logger()


class RagTool(ToolManager):
    "Rag Tool Manager class"

    def validate(self, index, tool_settings):
        """
        Validates a rag tool by performing a series of validation steps.

        Parameters:
            index (int): The index of the tool in the list.
            tool_settings (dict): The tool settings including configuration details.

        Returns:
            dict or None: A dictionary of tool information if validation is successful,
                None otherwise.
        """
        validation_steps = [
            self._validate_rag_tool_name,
            self._validate_rag_tool_version,
            self._validate_rag_tool_function_data,
        ]
        for step in validation_steps:
            error = step(
               index,
               tool_settings
            )
            if error:
                logger.error(error)
                return None
        return self._get_prompt_tool_info(index, tool_settings)

    def _validate_rag_tool_name(self, index, tool_settings):
        tool_name = self.tool_entry.get('name')
        settings_name = tool_settings.get('tool', {}).get('name')
        if tool_name != settings_name:
            return f"Tool name mismatch at index {index}: '{tool_name}' != '{settings_name}'"
        return None

    def _validate_rag_tool_version(self, index, tool_settings):
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

    def _validate_rag_tool_function_data(self, index, tool_settings):
        function_data = tool_settings.get('function')
        if not function_data:
            return f"Missing 'function' for tool {self.tool_entry.get('name')} at idx {index}."
        rag_data = function_data.get('rag')
        if not isinstance(rag_data, dict):
            return f"Invalid 'rag' type at index {index}. Expected a dictionary."
        file_data = tool_settings.get('data')
        if not isinstance(file_data, dict):
            return f"Invalid 'data files' type at index {index}. Expected a dictionary."
        return None

    def _get_prompt_tool_info(self, index, tool_settings):
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
            default_system_prompt = self._get_default_system_prompt()
            default_settings = self._get_default_settings()
            new_tool_info['settings']['function']['rag'] = (
                default_settings['function']['rag'])
            new_tool_info['settings']['function']['query_espantion'] = (
                default_system_prompt)
            new_tool_info['settings']['data']['files'] = (
                default_settings['data']['files'])
        return new_tool_info

    def _get_default_system_prompt(self):
        prompt_config = copy.deepcopy(CONFIG['prompts'])
        prompt_config['environment'] = self.tool_info['options']['default']['path']
        prompt_config['templates'] = self.tool_info['options']['default']['prompts']
        prompt = PromptRender.create(prompt_config)
        result = prompt.load('query_espantion')
        return result.content

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
            "function/query_espantion": tool_settings["query_espantion"],
            "function/rag/extractor": self._get_options("extractors", tool_settings["extractor"]),
            "function/rag/actions": tool_settings["actions"],
            "function/rag/retriever/n_results": tool_settings["n_results"],
            "function/rag/summary_chunks": tool_settings["summary_chunks"],
            "function/rag/storage": self._get_options("storages", tool_settings["storage"]),
            "function/rag/llm_model": self._get_options("llms", tool_settings["llm"]),
            "data/files": [{"source": file_name} for file_name in tool_settings["files"]],
        }
        base_url = self.tool_info.get('base_url')
        tool_discovery = ToolDiscovery(CONFIG["function"]["discovery"])
        response = tool_discovery.set_settings(base_url, config)
        tool_info = tool_discovery.get_settings(base_url)
        self. _load_files_into_db(tool_info)
        return response

    def _get_options(self, options, label):
        for llm in self.tool_info["options"][options]:
            if llm.get("label") == label:
                return llm.get("settings")
        return None

    def _load_files_into_db(self, config):
        collection = self._get_collection(config)
        for file in config["data"]["files"]:
            logger.info(f"Load file {file['source']}")
            file_name = file["source"]
            file_path = config["data"]["path"] + file_name
            elements = self._extract_file(config, file_path)
            transformed_elements = self._transform_elements(config, elements)
            self._load_elements(config, collection, transformed_elements)

    def _get_collection(self, config):
        config["function"]["rag"]["storage"]["reset"] = True
        data_storage= DataStorage.create(config["function"]["rag"]["storage"])
        result = data_storage.get_collection()
        return result.collection

    def _extract_file(self, config, file_path):
        data_extractor = DataExtractor.create(config["function"]["rag"]["extractor"])
        result = data_extractor.parse(file_path)
        return result.elements

    def _transform_elements(self, config, elements):
        data_transformer = DataTransformer.create(config["function"]["rag"]["transformer"])
        actions = config["function"]["rag"]["actions"]
        result = data_transformer.process(actions, elements)
        return result.elements

    def _load_elements(self, config, collection, elements):
        data_loader = DataLoader.create(config["function"]["rag"]["loader"])
        result = data_loader.insert(collection, elements)
        logger.debug(result.status)
