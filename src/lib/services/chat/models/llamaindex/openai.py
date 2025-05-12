#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LlamaIndex OpenAI Model

This module allows to:
- initialize the OpenAI environment variables
- return the LlamaIndexOpenAI model
- invoke a LLM to calculate the content of a prompt
"""

from typing import Optional, Dict, Any
from pydantic import Field
from llama_index.llms.openai import OpenAI
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel


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

    def invoke(self, message: str) -> 'LlamaIndexOpenAIModel.Result':
        """
        Call the LLM inference.

        :param message: Message to be processed by the model.
        :return: Result object containing the generated content.
        """
        try:
            self.result.status = "success"
            response = self.model.complete(message)
            self.result.content = response.text
            self.result.metadata = response.additional_kwargs
            logger.debug(f"Prompt generated {self.result.content}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking LLM: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_model(self) -> 'LlamaIndexOpenAIModel.Result':
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
