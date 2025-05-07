#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Nvidia Model

This module allows you to:
- Initialize the Nvidia API environment variables
- Return the LangChain Nvidia model
- Invoke a Large Language Model (LLM) to process a prompt
"""

import os
from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel


logger = Logger().get_logger()


class LangChainChatNvidiaModel(BaseChatModel):
    """
    Class for LangChain ChatMistralAI Model.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LangChainChatNvidiaModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainChatNvidiaModel.Config(**config)
        self.result = LangChainChatNvidiaModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> ChatNVIDIA:
        """
        Get the LangChain ChatNVIDIA model instance.

        :return: ChatNVIDIA model instance.
        """
        logger.debug("Selected LangChain ChatNVIDIA")
        os.environ["NVIDIA_API_KEY"] = self.config.api_key
        args = self._init_model_arguments()
        return ChatNVIDIA(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatNVIDIA model.

        :return: Dictionary of arguments for ChatNVIDIA.
        """
        args = {"model": self.config.model_name}
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        return args

    def invoke(self, message: str) -> 'LangChainChatNvidiaModel.Result':
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

    def get_model(self) -> 'LangChainChatNvidiaModel.Result':
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
