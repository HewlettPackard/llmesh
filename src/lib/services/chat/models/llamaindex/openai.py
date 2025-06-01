#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LlamaIndex OpenAI Model

This module allows to:
- initialize the OpenAI environment variables
- return the LlamaIndexOpenAI model
- invoke a LLM to calculate the content of a prompt
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Iterator, AsyncIterator
from pydantic import Field
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage, MessageRole
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel
from src.lib.services.chat.models.error_handler import model_error_handler, stream_error_handler


logger = Logger().get_logger()


class LlamaIndexOpenAIModel(BaseChatModel):
    """
    Class for LlamaIndexOpenAI Model.
    """

    class Config(BaseChatModel.Config):
        """
        Configuration for the Chat Model class.
        """
        system_prompt: Optional[str] = Field(
            None,
            description="System Prompt for the LLM"
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LlamaIndexOpenAI with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LlamaIndexOpenAIModel.Config(**config)
        self.result = LlamaIndexOpenAIModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> OpenAI:
        """
        Get the LlamaIndexOpenAI model instance.

        :return: OpenAI model instance.
        """
        logger.debug("Selected LlamaIndex OpenAI")
        args = self._init_model_arguments()
        return OpenAI(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatOpenAI model.

        :return: Dictionary of arguments for ChatOpenAI.
        """
        args = {
            "system_prompt": self.config.system_prompt,
            "model": self.config.model_name,
            "api_key": self.config.api_key
        }
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        return args

    def get_model(self) -> LlamaIndexOpenAIModel.Result:
        """
        Return the LLM model instance.

        :return: Result object containing the model instance.
        """
        self.result.model = self.model
        if self.model:
            self.result.status = "success"
            logger.debug(f"Returned model '{self.config.model_name}'")
        else:
            self.result.status = "failure"
            logger.error("No model present")
        return self.result

    @model_error_handler("An error occurred while invoking LLM")
    def invoke(self, messages: Any) -> LlamaIndexOpenAIModel.Result:
        """
        Call the LLM inference.

        :param messages: Messages to be processed by the model.
        :return: Result object containing the generated content.
        """
        self.result.status = "success"
        normalized_messages = self._normalize_messages(messages)
        response = self.model.chat(normalized_messages)
        self.result.content = response.text
        self.result.metadata = response.additional_kwargs
        logger.debug(f"Prompt generated {self.result.content}")
        return self.result

    @stream_error_handler("Streaming error")
    def stream(self, messages: Any) -> Iterator[str]:
        '''
        Synchronously stream the model response token by token.

        :param messages: Message string or list formatted for the model.
        :return: Iterator yielding response chunks.
        '''
        normalized_messages = self._normalize_messages(messages)
        for chunk in self.model.stream_chat(normalized_messages):
            yield chunk.delta

    @model_error_handler("An error occurred while async invoking LLM")
    async def ainvoke(self, messages: Any) -> LlamaIndexOpenAIModel.Result:
        '''
        Asynchronously invoke the model with a list of messages.

        :param messages: Message string or list formatted for the model.
        :return: Result object with content and metadata.
        '''
        self.result.status = "success"
        normalized_messages = self._normalize_messages(messages)
        response = await self.model.achat(normalized_messages)
        self.result.content = response.text
        self.result.metadata = response.additional_kwargs
        logger.debug(f"Async prompt generated: {self.result.content}")
        return self.result

    @stream_error_handler("Async streaming error")
    async def astream(self, messages: Any) -> AsyncIterator[str]:
        '''
        Asynchronously stream the model response token by token.

        :param messages: Message string or list formatted for the model.
        :return: Async iterator yielding response chunks.
        '''
        normalized_messages = self._normalize_messages(messages)
        stream_gen = await self.model.astream_chat(normalized_messages)
        async for chunk in stream_gen:
            yield chunk.delta

    def _normalize_messages(self, messages: Any) -> list:
        """
        Normalize input messages to a list of ChatMessage.

        :param messages: A string, a ChatMessage, or a list of them.
        :return: List of ChatMessage objects.
        """
        if isinstance(messages, str):
            return [ChatMessage(role=MessageRole.USER, content=messages)]
        elif isinstance(messages, ChatMessage):
            return [messages]
        elif isinstance(messages, list):
            return [
                ChatMessage(role=MessageRole.USER, content=m) if isinstance(m, str) else m
                for m in messages
            ]
        else:
            raise TypeError("Messages must be a string, ChatMessage, or list of those.")
