#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangchainChatOpenAI Model

This module allows to:
- initialize the OpenAI environment variables
- return the LangchainChatOpenAI model
- invoke a LLM to calculate the content of a prompt
"""

import os
from typing import Optional, Dict, Any
import httpx
from pydantic import Field
from langchain_openai import ChatOpenAI
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel


logger = Logger().get_logger()


class LangChainChatOpenAIModel(BaseChatModel):
    """
    Class for LangChain_ChatOpenAI Model.
    """

    class Config(BaseChatModel.Config):
        """
        Configuration for the Chat Model class.
        """
        base_url: Optional[str] = Field(
            None,
            description="Endpoint for the model API."
        )
        seed: Optional[int] = Field(
            None,
            description="Seed for model randomness."
        )
        https_verify: Optional[bool] = Field(
            None,
            description="Flag to enable or disable the TLS verification."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LangChainChatOpenAIModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainChatOpenAIModel.Config(**config)
        self.result = LangChainChatOpenAIModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> ChatOpenAI:
        """
        Get the Langchain ChatOpenAI model instance.

        :return: ChatOpenAI model instance.
        """
        logger.debug("Selected Langchain ChatOpenAI")
        os.environ["OPENAI_API_KEY"] = self.config.api_key
        args = self._init_model_arguments()
        return ChatOpenAI(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatOpenAI model.

        :return: Dictionary of arguments for ChatOpenAI.
        """
        args = {"model_name": self.config.model_name}
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        if self.config.seed is not None:
            args["seed"] = self.config.seed
        if self.config.base_url is not None:
            args["base_url"] = self.config.base_url
        if self.config.https_verify is not None:
            args["http_client"] = httpx.Client(verify=self.config.https_verify)
        return args

    def invoke(self, message: str) -> 'LangChainChatOpenAIModel.Result':
        """
        Call the LLM inference.

        :param message: Message to be processed by the model.
        :return: Result object containing the generated content.
        """
        try:
            self.result.status = "success"
            response = self.model.invoke(message)
            self.result.content = response.content
            self.result.metadata = response.response_metadata
            logger.debug(f"Prompt generated {self.result.content}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking LLM: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_model(self) -> 'LangChainChatOpenAIModel.Result':
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
