#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LlamaIndex Chat Message Manager

Handles message creation, conversion, and formatting using the LlamaIndex framework.
"""

from typing import List
from llama_index.core.llms import ChatMessage as LlamaMessage
from src.lib.services.chat.message_managers.base import (
    BaseMessageManager,
    SharedLogicMessageManager
)
from src.lib.services.chat.message_managers.message import (
    ChatMessage,
    MessageRole,
    TextBlock
)


class LlamaIndexChatMessageManager(BaseMessageManager):
    """
    Message manager implementation for LlamaIndex-compatible messages.
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

    def to_framework_messages(self, messages: List[ChatMessage]) -> BaseMessageManager.Result:
        """
        Convert internal ChatMessages into LlamaIndex-compatible messages.

        :param messages: List of internal ChatMessage objects.
        :return: List of LlamaIndex ChatMessage objects.
        """
        try:
            llama_msgs = []
            for msg in messages:
                if not isinstance(msg, ChatMessage):
                    raise TypeError("Invalid message type")
                llama_msgs.append(LlamaMessage(role=msg.role.value, content=msg.to_text()))
            self.result.status = "success"
            self.result.messages = llama_msgs
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = str(e)
        return self.result

    def from_framework_messages(self, messages: List[LlamaMessage]) -> BaseMessageManager.Result:
        """
        Convert LlamaIndex messages into internal ChatMessages.

        :param messages: List of LlamaIndex ChatMessage objects.
        :return: List of internal ChatMessage objects.
        """
        try:
            result = []
            for msg in messages:
                try:
                    role = MessageRole(msg.role)
                except ValueError:
                    role = MessageRole.USER
                result.append(
                    ChatMessage(
                        role=role,
                        blocks=[TextBlock(text=msg.content)]
                    )
                )
            self.result.status = "success"
            self.result.messages = result
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = str(e)
        return self.result
