#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool Repository Module

This module defines the ToolRepository class and associated classes for
managing different tools.
It utilizes the Factory Pattern to allow for flexible instantiation of tools
based on the configuration.
"""

from typing import Type, Dict, Any
from src.lib.services.agents.tool_repositories.langchain.structured_tool import (
    LangChainStructuredToolRepository)


class ToolRepository:  # pylint: disable=R0903
    """
    A tool repository class that uses a factory pattern to return
    the selected tool based on the provided configuration.
    """

    _repositories: Dict[str, Type] = {
        'LangChainStructured': LangChainStructuredToolRepository,
    }

    @staticmethod
    def create(config: Dict[str, Any]) -> object:
        """
        Return the appropriate tool based on the provided configuration.

        :param config: Configuration dictionary containing the type of tool.
        :return: An instance of the selected tool.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        repository_type = config.get('type')
        if not repository_type:
            raise ValueError("Configuration must include 'type'.")
        repository_class = ToolRepository._repositories.get(repository_type)
        if not repository_class:
            raise ValueError(f"Unsupported extractor type: {repository_type}")
        return repository_class(config)
