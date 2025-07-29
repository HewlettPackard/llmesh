#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Summary Memory

This module allows to:
- initialize and return the LangChain summary memory
"""

from __future__ import annotations
from typing import Dict, Optional, Any
from pydantic import Field
from langchain_core.messages import BaseMessage
from langchain.memory import ConversationSummaryMemory
from src.lib.services.core.log import Logger
from src.lib.services.chat.model import ChatModel
from src.lib.services.chat.memories.base import BaseChatMemory
from src.lib.services.chat.memories.error_handler import memory_error_handler


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

    def get_memory(self) -> LangChainSummaryMemory.Result:
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

    def clear(self) -> LangChainSummaryMemory.Result:
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
    def save_message(self, message: Any) -> LangChainSummaryMemory.Result:
        """
        Save a new message to the summary memory.

        :param message: The message object to save (should be a BaseMessage).
        :return: Result object containing the status of the save operation.
        """
        self.result.status = "success"
        if not isinstance(message, BaseMessage):
            raise TypeError(
                f"Expected message of type BaseMessage, got {type(message).__name__}"
            )
        # Add message to underlying chat memory
        self.memory.chat_memory.add_message(message)  # pylint: disable=E1101
        logger.debug("Message saved to summary memory")
        return self.result

    @memory_error_handler("Error retrieving message")
    def get_messages(self, limit: Optional[int] = None) -> LangChainSummaryMemory.Result:
        """
        Retrieve messages from summary memory.
        :param limit: Optional max number of messages to return.
        :return: Result object containing a list of messages.
        """
        self.result.status = "success"
        # Return messages if return_messages=True, otherwise return the summary
        if getattr(self.memory, "return_messages", False):
            messages = self.memory.chat_memory.messages  # pylint: disable=E1101
            if limit is not None:
                messages = messages[-limit:]
            self.result.messages = messages
            logger.debug(f"Retrieved {len(messages)} messages from summary memory")
        else:
            # If not returning messages, provide the summary buffer string
            self.result.messages = self.memory.buffer
            logger.debug(f"Retrieved summary from memory: {self.memory.buffer}")
        return self.result
