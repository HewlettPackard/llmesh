#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LlamaIndex Buffer Memory

This module allows to:
- initialize and return the LlamaIndex buffer memory
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import Field
from llama_index.core.llms import ChatMessage
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from src.lib.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory
from src.lib.services.chat.memories.error_handler import memory_error_handler


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

    def get_memory(self) -> LlamaIndexBufferMemory.Result:
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

    def clear(self) -> LlamaIndexBufferMemory.Result:
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

    @memory_error_handler("Error saving message")
    def save_message(self, message: Any) -> LlamaIndexBufferMemory.Result:
        """
        Save a single ChatMessage to the LlamaIndex buffer memory.

        :param message: A ChatMessage object.
        :return: Result object with save status.
        """
        self.result.status = "success"
        if not isinstance(message, ChatMessage):
            raise TypeError(
                f"Expected message of type ChatMessage, got {type(message).__name__}"
            )
        self.memory.put(message)
        logger.debug("ChatMessage saved to LlamaIndex buffer memory")
        return self.result

    @memory_error_handler("Error retrieving message")
    def get_messages(self, limit: Optional[int] = None) -> LlamaIndexBufferMemory.Result:
        """
        Retrieve messages from the LlamaIndex buffer memory.

        :param limit: Optional max number of messages to return.
        :return: Result object containing a list of ChatMessage.
        """
        self.result.status = "success"
        chat_turns = self.memory.get_all()
        messages = []
        for turn in chat_turns:
            messages.append(turn)
        if limit is not None:
            messages = messages[-limit:]
        self.result.messages = messages
        logger.debug(f"Retrieved {len(messages)} ChatMessage(s) from LlamaIndex buffer memory")
        return self.result
