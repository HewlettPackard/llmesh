#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class BaseReasoningEngine(abc.ABC):
    """
    Abstract base class for reasoning engines.
    """

    class Config(BaseModel):
        """
        Main configuration model for the reasoning engine.
        """
        type: str = Field(
            ...,
            description="Type of the reasoning engine."
        )
        system_prompt: str = Field(
            ...,
            description="System prompt used by the engine."
        )
        model: Dict[str, Any] = Field(
            ...,
            description="Dictionary containing model-specific configuration."
        )
        memory: Dict[str, Any] = Field(
            ...,
            description="Dictionary containing memory-specific configuration."
        )
        tools: Dict[str, Any] = Field(
            ...,
            description="Dictionary containing tools-specific configuration."
        )
        verbose: Optional[bool] = Field(
            default=False,
            description="Boolean flag to control verbosity of the system logs."
        )

    class Result(BaseModel):
        """
        Result of the reasoning engine invocation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        completion: Optional[str] = Field(
            None,
            description="Completion of the reasoning process."
        )

    @abc.abstractmethod
    def run(self, message: str) -> 'BaseReasoningEngine.Result':
        """
        Run the reasoning engine.

        :param message: Message to be processed by the engine.
        :return: Result object containing the outcome of the reasoning process.
        """

    @abc.abstractmethod
    def clear_memory(self) -> None:
        """
        Clear the memory of the reasoning engine.
        """

    @abc.abstractmethod
    def set_memory(self, memory: Dict[str, Any]) -> None:
        """
        Set the memory configuration of the engine.

        :param memory: Memory configuration dictionary.
        """

    @abc.abstractmethod
    def set_tools(self, tool_list: List[Any]) -> None:
        """
        Set the tools for the reasoning engine.

        :param tool_list: List of tools to be used by the engine.
        """
