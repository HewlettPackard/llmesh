#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain ChatMistralAI Model

This module allows you to:
- Initialize the Mistral AI  environment variables
- Return the LangChain ChatMistralAI model
- Invoke a Large Language Model (LLM) to process a prompt
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field
from langchain_mistralai import ChatMistralAI
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel


logger = Logger().get_logger()


class LangChainChatMistralAIModel(BaseChatModel):
    """
    Class for LangChain ChatMistralAI Model.
    """

    class Config(BaseChatModel.Config):
        """
        Configuration for the Chat Model class.
        """
        max_retries: Optional[int] = Field(
            None,
            description="Max retries on API."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LangChainChatMistralAIModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainChatMistralAIModel.Config(**config)
        self.result = LangChainChatMistralAIModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> ChatMistralAI:
        """
        Get the LangChain ChatMistralAI model instance.

        :return: ChatMistralAI model instance.
        """
        logger.debug("Selected LangChain ChatMistralAI")
        os.environ["MISTRAL_API_KEY"] = self.config.api_key
        args = self._init_model_arguments()
        return ChatMistralAI(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatMistralAI model.

        :return: Dictionary of arguments for ChatMistralAI.
        """
        args = {"model": self.config.model_name}
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        if self.config.max_retries is not None:
            args["max_retries"] = self.config.max_retries
        return args

    def invoke(self, message: str) -> 'LangChainChatMistralAIModel.Result':
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

    def get_model(self) -> 'LangChainChatMistralAIModel.Result':
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
