#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create tools array for HPE Athonet LLM Platform.

This script is part of the HPE Athonet LLM Platform's reasoning engine.
It dynamically searches and imports tools from:
- the 'tools' directory
- the 'tools' URL
Each tool, structured with a 'config.yaml' containing configuration and a 'function.py'
defining functionality and wrapped into AthonTool, is loaded into the system.
This allows for modular and scalable integration of various tools.
"""

import os
import importlib.util
from typing import Dict, Any, Tuple, Type, Optional
import requests
# from pydantic.v1 import BaseModel, Field, create_model
from pydantic import BaseModel, Field, create_model
from langchain.tools import StructuredTool
from src.lib.core.log import Logger


logger = Logger().get_logger()


class ToolDiscovery:
    """
    Class for discovering and loading tools in the Athonet LLM Platform.
    """

    class Config(BaseModel):
        """
        Configuration for the ToolDiscovery class.
        """
        timeout: Optional[int] = Field(
            10,
            description="Request timeout in seconds."
        )
        cert_verify: Optional[bool] = Field(
            True,
            description="Flag to verify SSL certificates for requests."
        )

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the ToolDiscovery instance with a configuration.

        :param config: A dictionary with configuration settings.
        """
        self.config = ToolDiscovery.Config(**(config or {}))

    def discover_tool(self, tool_reference: str) -> Dict[str, Any]:
        """
        Discover and load a tool to integrate into the reasoning engine.

        :param tool_reference: The path or URL to the tool.
        :return: A dictionary with the tool's name, tool object, and interface (if available).
        """
        tool_info = {}
        if tool_reference.startswith("http"):
            # It's a URL for a tool with a REST API
            tool_object, tool_interface = self._load_remote_tool(tool_reference)
        else:
            # It's a local tool
            tool_object, tool_interface = self._load_local_tool(tool_reference)
        if tool_object:
            logger.info(f"Discovered tool: {tool_object.name}")
            tool_info["name"] = tool_object.name
            tool_info["tool"] = tool_object
            if tool_interface:
                tool_info["interface"] = tool_interface
        return tool_info

    def _load_local_tool(self, tool_path: str) -> Tuple[Optional[StructuredTool], Optional[Dict]]:
        """
        Load a local tool from the specified path.

        :param tool_path: The path to the tool directory.
        :return: A tuple containing the tool object and interface (if available).
        """
        module_path = os.path.join(tool_path, "main.py")
        module_name = tool_path.replace(os.sep, "_") + "_manifest"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        tool_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool_module)
        manifest = tool_module.main(True)
        tool_object = self._create_tool_from_local_manifest(manifest)
        logger.info(f"Loaded tool: {manifest['name']} from {tool_path}")
        interface = manifest.get("interface")
        return tool_object, interface

    def _create_tool_from_local_manifest(self, manifest: Dict[str, Any]) -> StructuredTool:
        """
        Create a tool object based on the configuration in the provided manifest.

        :param manifest: A dictionary containing the tool's configuration.
        :return: A StructuredTool object representing the tool.
        """
        args_schema = self._create_args_schema(manifest['name'], manifest['arguments'])
        logger.debug(f"Created tool: {manifest['name']}")
        tool = StructuredTool.from_function(
            name=manifest['name'],
            args_schema=args_schema,
            func=manifest['function'],
            description=manifest['description'],
            return_direct=manifest['return_direct']
        )
        return tool

    def _load_remote_tool(self, tool_url: str) -> Tuple[Optional[StructuredTool], Optional[Dict]]:
        """
        Load a remote tool from the specified URL.

        :param tool_url: The base URL of the remote tool.
        :return: A tuple containing the tool object and interface (if available).
        """
        try:
            manifest = self._fetch_remote_manifest(tool_url + "manifest")
            tool_object = self._create_tool_from_remote_manifest(tool_url + "tool", manifest)
            logger.info(f"Loaded remote tool: {manifest['name']} from {tool_url}")
            interface = manifest.get("interface")
            return tool_object, interface
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"Failed to load tool from {tool_url}: {str(e)}")
            return None, None

    def _fetch_remote_manifest(self, manifest_url: str) -> Dict[str, Any]:
        """
        Fetch the manifest of a remote tool.

        :param manifest_url: The URL to the tool's manifest.
        :return: A dictionary containing the manifest data.
        """
        response = requests.get(
            manifest_url,
            timeout=self.config.timeout,
            verify=self.config.cert_verify)
        if response.ok:
            logger.debug(f"Fetched manifest from: {manifest_url}")
            return response.json()
        response.raise_for_status()
        return {}

    def _create_tool_from_remote_manifest(
            self,
            tool_url: str,
            manifest: Dict[str, Any]
        ) -> StructuredTool:
        """
        Create a tool object based on the configuration in the remote manifest.

        :param tool_url: The URL to the tool's tool endpoint.
        :param manifest: A dictionary containing the tool's configuration.
        :return: A StructuredTool object representing the tool.
        """
        args_schema = self._create_args_schema(manifest['name'], manifest['arguments'])

        def invoke_tool_via_api(*args, **kwargs):  # pylint: disable=W0613
            response = requests.post(
                tool_url,
                json=kwargs,
                timeout=self.config.timeout,
                verify=self.config.cert_verify
            )
            if response.ok:
                return response.text
            response.raise_for_status()
            return None

        logger.debug(f"Created remote tool: {manifest['name']}")
        tool = StructuredTool.from_function(
            name=manifest['name'],
            args_schema=args_schema,
            func=invoke_tool_via_api,
            description=manifest['description'],
            return_direct=manifest.get('return_direct', False)
        )
        return tool

    def _create_args_schema(self, tool_name: str, arguments: list) -> Type[BaseModel]:
        """
        Dynamically create a Pydantic model for the tool's arguments.

        :param tool_name: The name of the tool.
        :param arguments: A list of dictionaries defining the tool's arguments.
        :return: A dynamically created Pydantic model representing the arguments schema.
        """
        fields: Dict[str, Tuple[Any, ...]] = {}
        for arg in arguments:
            field_type = eval(arg['type'])  # pylint: disable=W0123
            default = arg.get('default', ...)
            description = arg.get('description', '')
            field_constraints = {}
            for constraint in arg.get('fields', []):
                for key, value in constraint.items():
                    field_constraints[key] = value
            fields[arg['name']] = (
                field_type,
                Field(default, description=description, **field_constraints)
            )
        logger.debug(f"Created argument schema for tool: {tool_name}")
        return create_model(f'{tool_name}ArgsSchema', **fields)

    def get_settings(self, tool_reference: str) -> Dict[str, Any]:
        """
        Get the settings of the tool specified.

        :param tool_reference: The path or URL to the tool.
        :return: A dictionary with the tool's settings.
        """
        if tool_reference.startswith("http"):
            # It's a URL for a tool with a REST API
            config_url = f"{tool_reference}/settings"
            response = requests.get(
                config_url,
                timeout=self.config.timeout,
                verify=self.config.cert_verify)
            if response.ok:
                logger.debug(f"Fetched settings from: {config_url}")
                return response.json()
            response.raise_for_status()
        else:
            # It's a local tool
            logger.error("Local tool not supported")
            raise ValueError("Local tool not supported")
        return {}

    def set_settings(self, tool_reference: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the settings of the tool specified.

        :param tool_reference: The path or URL to the tool.
        :param settings: The dict with the settings to update
        :return: The tool client response.
        """
        if tool_reference.startswith("http"):
            # It's a URL for a tool with a REST API
            config_url = f"{tool_reference}/settings"
            response = requests.post(
                config_url,
                json=settings,
                timeout=self.config.timeout,
                verify=self.config.cert_verify)
            if response.ok:
                logger.debug(f"Updated settings to: {config_url}")
                return response.json()
            response.raise_for_status()
        else:
            # It's a local tool
            logger.error("Local tool not supported")
            raise ValueError("Local tool not supported")
        return {}
