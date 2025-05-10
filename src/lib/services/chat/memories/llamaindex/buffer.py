#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LlamaIndex Buffer Memory

This module allows to:
- initialize and return the LlamaIndex buffer memory
"""

from typing import Any, Dict, Optional
from pydantic import Field
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from src.lib.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory


logger = Logger().get_logger()


class LlamaIndexBufferMemory(BaseChatMemory):
    """
    Class for LlamaIndex Buffer Memory Model.
    """

    class Config(BaseChatMemory.Config):
        """
        Configuration for the Chat Memory class.
        """
        token_limit: Optional[int] = Field(
            default=None,
            description="Max number of token to store."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the memory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        self.config = LlamaIndexBufferMemory.Config(**config)
        self.result = LlamaIndexBufferMemory.Result()
        self.memory = self._init_memory()

    def _init_memory(self) -> ChatMemoryBuffer:
        """
        Initialize and return the ChatMemoryBuffer instance.

        :return: ChatMemoryBuffer instance.
        """
        logger.debug("Selected LlamaIndex Buffer Memory")
        chat_store = SimpleChatStore()
        return ChatMemoryBuffer.from_defaults(
            token_limit=self.config.token_limit,
            chat_store=chat_store,
            chat_store_key=self.config.memory_key,
        )

    def get_memory(self) -> 'LlamaIndexBufferMemory.Result':
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

    def clear(self) -> 'LlamaIndexBufferMemory.Result':
        """
        Clear context memory.

        :return: Result object containing the status of the clear operation.
        """
        if self.memory:
            self.memory.reset()
            self.result.status = "success"
            logger.debug("Cleared memory")
        else:
            self.result.status = "failure"
            self.result.error_message = "No memory present"
            logger.error(self.result.error_message)
        return self.result
