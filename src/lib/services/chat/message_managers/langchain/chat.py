#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Chat Message Manager

Handles message creation, conversion, and formatting using the LangChain framework.
"""

from typing import List, Any
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from src.lib.services.chat.message_managers.base import (
    BaseMessageManager,
    SharedLogicMessageManager
)
from src.lib.services.core.log import Logger
from src.lib.services.chat.message_managers.message import (
    ChatMessage,
    MessageRole,
    TextBlock
)


logger = Logger().get_logger()


class LangChainChatMessageManager(BaseMessageManager):
    """
    Message manager implementation for LangChain messages.
    """

    def __init__(self, config: dict) -> None:
        self.shared = SharedLogicMessageManager(config)
        self.config = self.shared.config
        self.result = self.shared.result

    def create_message(self, role: MessageRole, content: str) -> BaseMessageManager.Result:
        return self.shared.create_message(role, content)

    def add_messages(
        self,
        messages: List[ChatMessage],
        new_messages: List[ChatMessage],
        index: int = None
    ) -> BaseMessageManager.Result:
        return self.shared.add_messages(messages, new_messages, index)

    def dump_messages(self, messages: List[ChatMessage]) -> BaseMessageManager.Result:
        return self.shared.dump_messages(messages)

    def load_messages(self, data: List[dict]) -> BaseMessageManager.Result:
        return self.shared.load_messages(data)

    def to_framework_messages(self, messages: List[ChatMessage]) -> List[Any]:
        """
        Convert internal ChatMessages into LangChain-compatible messages.

        :param messages: List of internal ChatMessage objects.
        :return: List of LangChain message objects.
        """
        result = []
        for msg in messages:
            if not isinstance(msg, ChatMessage):
                logger.warning(f"Skipped not valid message: {msg}")
                continue  # skip invalid types
            text = msg.to_text()
            if msg.role == MessageRole.USER:
                result.append(HumanMessage(content=text))
            elif msg.role == MessageRole.ASSISTANT:
                result.append(AIMessage(content=text))
            elif msg.role == MessageRole.SYSTEM:
                result.append(SystemMessage(content=text))
        return result

    def from_framework_messages(self, messages: List[Any]) -> List[ChatMessage]:
        """
        Convert LangChain messages into internal ChatMessages.

        :param messages: List of LangChain message objects.
        :return: List of internal ChatMessage objects.
        """
        converted = []
        for msg in messages:
            role = (
                MessageRole.USER if isinstance(msg, HumanMessage) else
                MessageRole.ASSISTANT if isinstance(msg, AIMessage) else
                MessageRole.SYSTEM if isinstance(msg, SystemMessage) else
                MessageRole.USER  # fallback
            )
            converted.append(ChatMessage(role=role, blocks=[TextBlock(text=msg.content)]))
        return converted
