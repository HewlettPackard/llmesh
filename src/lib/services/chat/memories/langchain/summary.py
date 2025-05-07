#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Summary Memory

This module allows to:
- initialize and return the LangChain summary memory
"""

from typing import Dict, Optional, Any
from pydantic import Field
from langchain.memory import ConversationSummaryMemory
from src.lib.core.log import Logger
from src.lib.services.chat.model import ChatModel
from src.lib.services.chat.memories.base import BaseChatMemory


logger = Logger().get_logger()


class LangChainSummaryMemory(BaseChatMemory):
    """
    Class for LangChain Summary Memory Model.
    """

    class Config(BaseChatMemory.Config):
        """
        Configuration for the Chat Memory class.
        """
        llm_model: Dict = Field(
            ...,
            description="Configuration of LLM model used to create the summary."
        )
        buffer: Optional[str] = Field(
            None,
            description="Initial summary."
        )
        return_messages: Optional[bool] = Field(
            default=True,
            description="Flag to determine if messages should be returned."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the memory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        self.config = LangChainSummaryMemory.Config(**config)
        self.result = LangChainSummaryMemory.Result()
        self.llm = self._init_llm()
        self.memory = self._init_memory()

    def _init_llm(self) -> object:
        """
        Initialize and return the LLM model.

        :return: LLM model instance.
        """
        return ChatModel().create(self.config.llm_model)

    def _init_memory(self) -> ConversationSummaryMemory:
        """
        Initialize and return the ConversationSummaryMemory instance.

        :return: ConversationSummaryMemory instance.
        """
        logger.debug("Selected LangChain Summary Memory")
        result = self.llm.get_model()
        return ConversationSummaryMemory(
            llm=result.model,
            buffer=self.config.buffer,
            return_messages=self.config.return_messages,
            memory_key=self.config.memory_key
        )

    def get_memory(self) -> 'LangChainSummaryMemory.Result':
        """
        Return the memory instance.

        :return: Result object containing the memory instance.
        """
        self.result.memory = self.memory
        if self.memory:
            self.result.status = "success"
            logger.debug(f"Returned memory '{self.config.type}'")
        else:
            self.result.status = "failure"
            self.result.error_message = "No memory present"
            logger.error(self.result.error_message)
        return self.result

    def clear(self) -> 'LangChainSummaryMemory.Result':
        """
        Clear context memory.

        :return: Result object containing the status of the clear operation.
        """
        if self.memory:
            self.memory.clear()
            self.result.status = "success"
            logger.debug("Cleared memory")
        else:
            self.result.status = "failure"
            self.result.error_message = "No memory present"
            logger.error(self.result.error_message)
        return self.result
