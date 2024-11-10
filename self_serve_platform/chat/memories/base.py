#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any
from pydantic import BaseModel, Field


class BaseChatMemory(abc.ABC):
    """
    Abstract base class for chat memory management.
    """

    class Config(BaseModel):
        """
        Configuration for the Chat Memory class.
        """
        type: str = Field(
            ...,
            description="Type of the memory."
        )
        memory_key: str = Field(
            ...,
            description="Key identifier for the memory, e.g., chat_history."
        )

    class Result(BaseModel):
        """
        Result of the Chat Memory operation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        context: Optional[Any] = Field(
            default=None,
            description="Memory context."
        )
        memory: Optional[Any] = Field(
            default=None,
            description="Instance of the Chat memory."
        )

    @abc.abstractmethod
    def get_memory(self) -> Any:
        """
        Return the memory instance.

        :return: The memory instance.
        """

    @abc.abstractmethod
    def clear(self) -> 'BaseChatMemory.Result':
        """
        Clear context memory.

        :return: Result object containing the status of the clear operation.
        """
