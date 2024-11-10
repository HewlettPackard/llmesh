#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Langchain_AzureChatOpenAI Model

This module allows to:
- initialize the AzureOpenAI environment variables
- return the Langchain_AzureChatOpenAI model
- invoke an LLM to calculate the content of a prompt
"""

import os
from typing import Dict, Any, Optional
from pydantic import Field
from langchain_openai import AzureChatOpenAI
from self_serve_platform.system.log import Logger
from self_serve_platform.chat.models.base import BaseChatModel


logger = Logger().get_logger()


class LangChainAzureChatOpenAIModel(BaseChatModel):
    """
    Class for LangChain_AzureChatOpenAI Model.
    """

    class Config(BaseChatModel.Config):
        """
        Configuration for the Chat Model class.
        """
        azure_deployment: str = Field(
            ...,
            description="Name of the deployment instance."
        )
        endpoint: str = Field(
            ...,
            description="Endpoint for the model API."
        )
        api_version: str = Field(
            ...,
            description="API version if applicable."
        )
        seed: Optional[int] = Field(
            None,
            description="Seed for model randomness."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LangChainAzureChatOpenAIModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainAzureChatOpenAIModel.Config(**config)
        self.result = LangChainAzureChatOpenAIModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> AzureChatOpenAI:
        """
        Initialize and return the model.

        :return: AzureChatOpenAI model instance.
        """
        logger.debug("Selected Langchain AzureChatOpenAI")
        os.environ["AZURE_OPENAI_API_KEY"] = self.config.api_key
        os.environ["AZURE_OPENAI_ENDPOINT"] = self.config.endpoint or "default_endpoint"
        args = self._init_model_arguments()
        return AzureChatOpenAI(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the AzureChatOpenAI model.

        :return: Dictionary of arguments for AzureChatOpenAI.
        """
        args = {
            "azure_deployment": self.config.azure_deployment,
            "api_version": self.config.api_version
        }
        # Add optional settings only if they are not None
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        if self.config.seed is not None:
            args["seed"] = self.config.seed
        return args

    def invoke(self, message: str) -> 'LangChainAzureChatOpenAIModel.Result':
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

    def get_model(self) -> 'LangChainAzureChatOpenAIModel.Result':
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