#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain ChatGoogleGenerativeAI Model

This module allows you to:
- Initialize the Google Gen AI environment variables
- Return the LangChain ChatGoogleGenerativeAI model
- Invoke a Large Language Model (LLM) to process a prompt
"""

import os
from typing import Optional, Dict, Any, Iterator, AsyncIterator
from pydantic import Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel


logger = Logger().get_logger()


class LangChainChatGoogleGenAIModel(BaseChatModel):
    """
    Class for LangChain ChatGoogleGenerativeAI Model.
    """

    class Config(BaseChatModel.Config):
        """
        Configuration for the Chat Model class.
        """
        max_tokens: Optional[int] = Field(
            None,
            description="Max number of tokens to return."
        )
        timeout: Optional[float] = Field(
            None,
            description="Timeout of generation."
        )
        max_retries: Optional[int] = Field(
            None,
            description="Max retries on API."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LangChainChatGoogleGenAIModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainChatGoogleGenAIModel.Config(**config)
        self.result = LangChainChatGoogleGenAIModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> ChatGoogleGenerativeAI:
        """
        Get the LangChain ChatGoogleGenerativeAI model instance.

        :return: ChatGoogleGenerativeAI model instance.
        """
        logger.debug("Selected LangChain ChatGoogleGenerativeAI")
        os.environ["GOOGLE_API_KEY"] = self.config.api_key
        args = self._init_model_arguments()
        return ChatGoogleGenerativeAI(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatGoogleGenerativeAI model.

        :return: Dictionary of arguments for ChatGoogleGenerativeAI.
        """
        args = {"model": self.config.model_name}
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            args["max_output_tokens"] = self.config.max_tokens
        if self.config.timeout is not None:
            args["timeout"] = self.config.timeout
        if self.config.max_retries is not None:
            args["max_retries"] = self.config.max_retries
        return args

    def get_model(self) -> 'LangChainChatGoogleGenAIModel.Result':
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
            logger.error("No model instance available")
        return self.result

    def invoke(self, messages: Any) -> 'LangChainChatGoogleGenAIModel.Result':
        """
        Invoke the LLM to process the given message.

        :param messages: Messages to be processed by the model.
        :return: Result object containing the generated content.
        """
        try:
            self.result.status = "success"
            response = self.model.invoke(messages)
            self.result.content = response.content
            self.result.metadata = response.response_metadata
            logger.debug(f"Generated response: {self.result.content}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking the LLM: {e}"
            logger.error(self.result.error_message)
        return self.result
    def stream(self, messages: Any) -> Iterator[str]:
        '''
        Synchronously stream the model response token by token.

        :param messages: Message list formatted for the model.
        :return: Iterator yielding response chunks.
        '''
        try:
            for chunk in self.model.stream(messages):
                yield chunk.content
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"Streaming error: {e}")
            raise

    async def ainvoke(self, messages: Any) -> 'LangChainChatGoogleGenAIModel.Result':
        '''
        Asynchronously invoke the model with a list of messages.

        :param messages: Message list formatted for the model.
        :return: Result object with content and metadata.
        '''
        try:
            self.result.status = "success"
            response = await self.model.ainvoke(messages)
            self.result.content = response.content
            self.result.metadata = response.response_metadata
            logger.debug(f"Async prompt generated: {self.result.content}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"Async error: {e}"
            logger.error(self.result.error_message)
        return self.result

    async def astream(self, messages: Any) -> AsyncIterator[str]:
        '''
        Asynchronously stream the model response token by token.

        :param messages: Message list formatted for the model.
        :return: Async iterator yielding response chunks.
        '''
        try:
            async for chunk in self.model.astream(messages):
                yield chunk.content
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"Async streaming error: {e}")
            raise
