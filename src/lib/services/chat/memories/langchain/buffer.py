#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Buffer Memory

This module allows to:
- initialize and return the LangChain buffer memory
"""

from typing import Any, Dict, Optional
from pydantic import Field
from langchain.memory import ConversationBufferMemory
from src.lib.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory


logger = Logger().get_logger()


class LangChainBufferMemory(BaseChatMemory):
    """
    Class for LangChain Buffer Memory Model.
    """

    class Config(BaseChatMemory.Config):
        """
        Configuration for the Chat Memory class.
        """
        return_messages: Optional[bool] = Field(
            default=True,
            description="Flag to determine if messages should be returned."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the memory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        self.config = LangChainBufferMemory.Config(**config)
        self.result = LangChainBufferMemory.Result()
        self.memory = self._init_memory()

    def _init_memory(self) -> ConversationBufferMemory:
        """
        Initialize and return the ConversationBufferMemory instance.

        :return: ConversationBufferMemory instance.
        """
        logger.debug("Selected LangChain Buffer Memory")
        return ConversationBufferMemory(
            return_messages=self.config.return_messages,
            memory_key=self.config.memory_key
        )

    def get_memory(self) -> 'LangChainBufferMemory.Result':
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

    def clear(self) -> 'LangChainBufferMemory.Result':
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
