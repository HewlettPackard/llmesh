#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Tool Repository

Abstract base class for tool repositories.
"""

import abc
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class BaseToolRepository(abc.ABC):
    """
    Abstract base class for tool repositories.
    """

    class Config(BaseModel):
        """
        Main configuration model for the tool repository.
        """
        type: str = Field(
            ...,
            description="Type of the tool repository."
        )

    class Result(BaseModel):
        """
        Result of the tool repository operation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        tools: Optional[Dict[str, Any]] = Field(
            None,
            description="List of tools."
        )

    @abc.abstractmethod
    def add_tool(
        self,
        tool: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> 'BaseToolRepository.Result':
        """
        Add a tool to the repository based on the provided configuration and metadata.

        :param tool: Tool object.
        :param metadata: Optional metadata dictionary to attach to the tool.
        """

    @abc.abstractmethod
    def get_tools(
        self,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> 'BaseToolRepository.Result':
        """
        Get the list of tools, optionally filtering by metadata.

        :param metadata_filter: Optional dictionary of metadata to filter tools.
        :return: List of tools that match the metadata filter.
        """
