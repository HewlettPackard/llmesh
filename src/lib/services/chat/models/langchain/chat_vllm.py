#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangchainChatVLLM Model

This module allows to:
- initialize the vLLM environment variables
- return the LangChainChatVLL model
- invoke a LLM to calculate the content of a prompt
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field
from langchain_community.llms.vllm import VLLM
from src.lib.core.log import Logger
from src.lib.services.chat.models.base import BaseChatModel


logger = Logger().get_logger()


class LangChainChatVLLMModel(BaseChatModel):
    """
    Class for LangChainChatVLLM Model.
    """

    class Config(BaseChatModel.Config):
        """
        Configuration for the Chat Model class.
        """
        trust_remote_code: Optional[bool] = Field(
            True,
            description="Trust flag mandatory for hf models"
        )
        tensor_parallel_size: Optional[int] = Field(
            None,
            description="The GPUs to use for distributed execution with tensor parallelism"
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LangChainChatOpenAIModel with the given configuration.

        :param config: Configuration dictionary for the model.
        """
        self.config = LangChainChatVLLMModel.Config(**config)
        self.result = LangChainChatVLLMModel.Result()
        self.model = self._init_model()

    def _init_model(self) -> VLLM:
        """
        Get the Langchain VLLM model instance.

        :return: VLLM model instance.
        """
        logger.debug("Selected Langchain VLLM")
        os.environ["OPENAI_API_KEY"] = self.config.api_key
        args = self._init_model_arguments()
        return VLLM(**args)

    def _init_model_arguments(self) -> Dict[str, Any]:
        """
        Create arguments for initializing the ChatOpenAI model.

        :return: Dictionary of arguments for ChatOpenAI.
        """
        args = {"model": self.config.model_name}
        if self.config.temperature is not None:
            args["temperature"] = self.config.temperature
        if self.config.trust_remote_code is not None:
            args["trust_remote_code"] = self.config.trust_remote_code
        if self.config.tensor_parallel_size is not None:
            args["tensor_parallel_size"] = self.config.tensor_parallel_size
        return args

    def invoke(self, message: str) -> 'LangChainChatVLLMModel.Result':
        """
        Call the LLM inference.

        :param message: Message to be processed by the model.
        :return: Result object containing the generated content.
        """
        try:
            self.result.status = "success"
            response = self.model.invoke(message)
            self.result.content = response
            self.result.metadata = {}
            logger.debug(f"Prompt generated {self.result.content}")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking LLM: {e}"
            logger.error(self.result.error_message)
        return self.result

    def get_model(self) -> 'LangChainChatVLLMModel.Result':
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
