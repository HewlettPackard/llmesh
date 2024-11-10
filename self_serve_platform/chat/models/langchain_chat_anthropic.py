#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain ChatAnthropic Model

This module allows you to:
- Initialize the Anthropic  environment variables
- Return the LangChain ChatAnthropic model
- Invoke a Large Language Model (LLM) to process a prompt
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field
from langchain_anthropic import ChatAnthropic
from self_serve_platform.system.log import Logger
from self_serve_platform.chat.models.base import BaseChatModel

logger = Logger().get_logger()


class LangChainChatAnthropicModel(BaseChatModel):
    """
    Class for LangChain ChatAnthropic Model.
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
        Initialize the LangChainChatAnthropicModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainChatAnthropicModel.Config(**config)
        self.result = LangChainChatAnthropicModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> ChatAnthropic:
        """
        Get the LangChain ChatAnthropic model instance.

        :return: ChatAnthropic model instance.
        """
        logger.debug("Selected LangChain ChatAnthropic")
        os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
        args = self._init_model_arguments()
        return ChatAnthropic(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatAnthropic model.

        :return: Dictionary of arguments for ChatAnthropic.
        """
        args = {"model": self.config.model_name}
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            args["max_tokens"] = self.config.max_tokens
        if self.config.timeout is not None:
            args["timeout"] = self.config.timeout
        if self.config.max_retries is not None:
            args["max_retries"] = self.config.max_retries
        return args

    def invoke(self, message: str) -> 'LangChainChatAnthropicModel.Result':
        """
        Invoke the LLM to process the given message.

        :param message: Message to be processed by the model.
        :return: Result object containing the generated content.
        """
        try:
            response = self.model.invoke(message)
            self.result.status = "success"
            self.result.content = response.content
            self.result.metadata = response.response_metadata
            logger.debug(f"Generated response: {self.result.content}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking the LLM: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_model(self) -> 'LangChainChatAnthropicModel.Result':
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