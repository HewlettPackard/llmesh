#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Buffer Window Memory

This module allows to:
- initialize and return the LangChain buffer window memory
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import Field
from langchain_core.messages import BaseMessage
from langchain.memory import ConversationBufferWindowMemory
from src.lib.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory
from src.lib.services.chat.memories.error_handler import memory_error_handler


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

    def get_memory(self) -> LangChainBufferWindowMemory.Result:
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

    def clear(self) -> LangChainBufferWindowMemory.Result:
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

    @memory_error_handler("Error saving message")
    def save_message(self, message: Any) -> LangChainBufferWindowMemory.Result:
        """
        Save a new message to the memory.

        :param message: The message object to save.
        :return: Result object containing the status of the save operation.
        """
        self.result.status = "success"
        if not isinstance(message, BaseMessage):
            raise TypeError(
                f"Expected message of type BaseMessage, got {type(message).__name__}"
            )
        self.memory.chat_memory.add_message(message)  # pylint: disable=E1101
        logger.debug("Message saved to buffer window memory")
        return self.result

    @memory_error_handler("Error retrieving message")
    def get_messages(self, limit: Optional[int] = None) -> LangChainBufferWindowMemory.Result:
        """
        Retrieve messages from buffer window memory.
        :param limit: Optional max number of messages to return.
        :return: Result object containing a list of messages.
        """
        self.result.status = "success"
        messages = self.memory.chat_memory.messages  # pylint: disable=E1101
        if limit is not None:
            messages = messages[-limit:]
        self.result.messages = messages
        logger.debug(f"Retrieved {len(messages)} messages from buffer window memory")
        return self.result
