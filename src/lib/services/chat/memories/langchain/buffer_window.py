#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Buffer Window Memory

This module allows to:
- initialize and return the LangChain buffer window memory
"""

from typing import Optional
from pydantic import Field
from langchain.memory import ConversationBufferWindowMemory
from src.lib.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory


logger = Logger().get_logger()


class LangChainBufferWindowMemory(BaseChatMemory):
    """
    Class for LangChain Buffer Window Memory Model.
    """

    class Config(BaseChatMemory.Config):
        """
        Configuration for the Chat Memory class.
        """
        window: int = Field(
            ...,
            description="Number of past interactions to consider in the memory window."
        )
        return_messages: Optional[bool] = Field(
            default=True,
            description="Flag to determine if messages should be returned."
        )

    def __init__(self, config: dict) -> None:
        """
        Initialize the memory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        self.config = LangChainBufferWindowMemory.Config(**config)
        self.result = LangChainBufferWindowMemory.Result()
        self.memory = self._init_memory()

    def _init_memory(self) -> ConversationBufferWindowMemory:
        """
        Initialize and return the ConversationBufferWindowMemory instance.

        :return: ConversationBufferWindowMemory instance.
        """
        logger.debug("Selected LangChain Buffer Window Memory")
        return ConversationBufferWindowMemory(
            return_messages=self.config.return_messages,
            memory_key=self.config.memory_key,
            k=self.config.window
        )

    def get_memory(self) -> 'LangChainBufferWindowMemory.Result':
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

    def clear(self) -> 'LangChainBufferWindowMemory.Result':
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
