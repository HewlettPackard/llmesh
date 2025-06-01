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
        memory: Optional[Any] = Field(
            default=None,
            description="Instance of the Chat memory."
        )
        messages: Optional[list] = Field(
            default=None,
            description="List of retrieved chat messages."
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

    @abc.abstractmethod
    def save_message(self, message: Any) -> 'BaseChatMemory.Result':
        """
        Save a new chat message to memory.
        :param message: The message object to save.
        :return: Result object indicating success or error.
        """

    @abc.abstractmethod
    def get_messages(self, limit: Optional[int] = None) -> 'BaseChatMemory.Result':
        """
        Retrieve messages from memory.
        :param limit: Optional max number of messages to return (default: all or as configured).
        :return: Result object containing a list of messages.
        """
