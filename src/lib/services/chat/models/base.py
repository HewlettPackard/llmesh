#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any, Iterator, AsyncIterator
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
        model_name: Optional[str] = Field(
            None,
            description="Name of the model deployment."
        )
        api_key: Optional[str] = Field(
            "",
            description="API key or JWT token for accessing the model."
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
        model: Optional[Any] = Field(
            None,
            description="Instance of the Chat model."
        )
        content: Optional[str] = Field(
            None,
            description="LLM completion content."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        metadata: Optional[str] = Field(
            None,
            description="LLM response metadata."
        )

    @abc.abstractmethod
    def get_model(self) -> Any:
        """
        Return the LLM model instance.

        :return: The LLM model instance.
        """

    @abc.abstractmethod
    def invoke(self, messages: Any) -> 'BaseChatModel.Result':
        """
        Synchronously invoke the model with a list of messages.

        :param messages: List of messages formatted for the LLM input.
        :return: Result object containing the generated content and metadata.
        """

    @abc.abstractmethod
    def stream(self, messages: Any) -> Iterator[str]:
        """
        Synchronously stream the model response token by token.

        :param messages: List of messages formatted for the LLM input.
        :return: Iterator that yields response chunks as strings.
        """

    @abc.abstractmethod
    async def ainvoke(self, messages: Any) -> 'BaseChatModel.Result':
        """
        Asynchronously invoke the model with a list of messages.

        :param messages: List of messages formatted for the LLM input.
        :return: Result object containing the generated content and metadata.
        """

    @abc.abstractmethod
    async def astream(self, messages: Any) -> AsyncIterator[str]:
        """
        Asynchronously stream the model response token by token.

        :param messages: List of messages formatted for the LLM input.
        :return: Async iterator that yields response chunks as strings.
        """
