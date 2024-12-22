#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any
from pydantic import BaseModel, Field


class BaseChatModel(abc.ABC):
    """
    Abstract base class for chat models.
    """

    class Config(BaseModel):
        """
        Configuration for the Chat Model class.
        """
        type: str = Field(
            ...,
            description="Type of the model deployment."
        )
        api_key: str = Field(
            ...,
            description="API key or JWT token for accessing the model."
        )
        model_name: Optional[str] = Field(
            None,
            description="Name of the model deployment."
        )
        temperature: Optional[float] = Field(
            None,
            description="Temperature setting for the model."
        )

    class Result(BaseModel):
        """
        Result of the Chat Model invocation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        content: Optional[str] = Field(
            None,
            description="LLM completion content."
        )
        metadata: Optional[str] = Field(
            None,
            description="LLM response metadata."
        )
        model: Optional[Any] = Field(
            None,
            description="Instance of the Chat model."
        )

    @abc.abstractmethod
    def get_model(self) -> Any:
        """
        Return the LLM model instance.

        :return: The LLM model instance.
        """

    @abc.abstractmethod
    def invoke(self, message) -> 'BaseChatModel.Result':
        """
        Invoke the LLM to create content.

        :param message: Message to be processed by the model.
        :return: Result object containing the generated content and model instance.
        """
