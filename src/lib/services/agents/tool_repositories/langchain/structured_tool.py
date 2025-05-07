#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool Repository Module

This module defines the LangChainStructuredToolRepository class and associated classes for
managing different tools.
It utilizes the Factory Pattern to allow for flexible instantiation of tools
based on the configuration and maintains a repository of tools with metadata.
"""

from typing import Dict, Any, Optional
import threading
from src.lib.core.log import Logger
from src.lib.services.agents.tool_repositories.base import BaseToolRepository


logger = Logger().get_logger()


class LangChainStructuredToolRepository(BaseToolRepository):
    """
    A singleton tool repository class that uses a factory pattern to manage
    tools and their metadata.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LangChainStructuredToolRepository, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Dict[str, Any] = None):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self.config = LangChainStructuredToolRepository.Config(**config) if config else None
            self.result = LangChainStructuredToolRepository.Result()
            self._tools = []
            self._metadata = {}
            self._initialized = True

    def add_tool(
            self,
            tool: Any,
            metadata: Optional[Dict[str, Any]] = None
        ) -> 'LangChainStructuredToolRepository.Result':
        """
        Add a tool to the repository based on the provided configuration and metadata.

        :param tool: tool object.
        :param metadata: Optional metadata dictionary to attach to the tool.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        try:
            self.result.status = "success"
            self._tools.append(tool)
            if metadata:
                self._metadata[tool.name] = metadata
            logger.debug("Added tool to repository")
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while adding a tool: {e}"
            logger.error(self.result.error_message)
        return self.result

    def update_tool(
            self,
            tool_name: str,
            new_tool: Optional[Any] = None,
            new_metadata: Optional[Dict[str, Any]] = None
        ) -> 'LangChainStructuredToolRepository.Result':
        """
        Update an existing tool's configuration or metadata in the repository.

        :param tool_name: The name of the tool to update.
        :param new_tool: An optional new tool object to replace the existing tool.
        :param new_metadata: Optional dictionary of metadata to update.
        :return: Result object indicating success or failure.
        """
        try:
            for i, tool in enumerate(self._tools):
                if tool.name == tool_name:
                    if new_tool:
                        self._tools[i] = new_tool
                        logger.debug(f"Updated tool '{tool_name}' configuration.")
                    if new_metadata:
                        self._metadata[tool_name] = {
                            **self._metadata.get(tool_name, {}),
                            **new_metadata
                        }
                        logger.debug(f"Updated metadata for tool '{tool_name}'.")
                    self.result.status = "success"
                    return self.result
            # Tool not found
            self.result.status = "failure"
            self.result.error_message = f"Tool '{tool_name}' not found in the repository."
            logger.error(self.result.error_message)
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while updating the tool: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_tools(
            self,
            metadata_filter: Optional[Dict[str, Any]] = None
        ) -> 'LangChainStructuredToolRepository.Result':
        """
        Get the list of tools, optionally filtering by metadata.

        :param metadata_filter: Optional dictionary of metadata to filter tools.
        :return: List of tools that match the metadata filter.
        """
        try:
            self.result.status = "success"
            filtered_tools = []
            for tool in self._tools:
                tool_metadata = self._metadata.get(tool.name, {})
                if (not metadata_filter
                    or all(item in tool_metadata.items() for item in metadata_filter.items())):
                    filtered_tools.append({
                        "object": tool,
                        "metadata": tool_metadata
                    })
            self.result.tools = filtered_tools
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while getting the tools: {e}"
            logger.error(self.result.error_message)
        return self.result
