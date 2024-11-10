#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class BaseMessageManager(abc.ABC):
    """
    Base class for message manager. This is an abstract class that needs to be extended.
    """

    class Config(BaseModel):
        """
        Base Configuration model for message formatter settings.
        """
        type: str = Field(
            ...,
            description="Type of the manager deployment."
        )
        json_convert: Optional[bool] = Field(
            default=False,
            description="Flag indicating if JSON conversion is required."
        )
        memory_key: Optional[str] = Field(
            default=None,
            description="Key identifier for the memory, e.g., chat_history."
        )

    class Result(BaseModel):
        """
        Base Results class.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        prompts: Optional[List[Any]] = Field(
            default=None,
            description="List of prompt objects or dictionaries of strings."
        )

    @abc.abstractmethod
    def convert_to_messages(self, prompts_dict: dict) -> 'BaseMessageManager.Result':
        """
        Convert dict of strings into a list of message objects

        :param prompts_dict: Dictionary containing the prompts data.
        :return: Result object containing the status and loaded prompts.
        """

    @abc.abstractmethod
    def convert_to_strings(self, prompts: List[Any]) -> 'BaseMessageManager.Result':
        """
        Convert a list of message objects into dict of strings

        :param prompts: List of prompt objects.
        :return: Result object containing the status and dumped prompts.
        """
