#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from src.lib.services.chat.message_managers.message import (
    ChatMessage,
    MessageRole,
    TextBlock
)
from src.lib.services.chat.message_managers.error_handler import message_error_handler


class BaseMessageManager(abc.ABC):
    """
    Base class for message manager. This is an abstract class that needs to be extended.
    """

    class Config(BaseModel):
        """
        Base Configuration model for message formatter settings.
        """
        type: str = Field(
            ...,
            description="Type of the manager deployment."
        )

    class Result(BaseModel):
        """
        Base Results class.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        messages: Optional[List[Any]] = Field(
            default=None,
            description="List of messages or dictionaries of strings."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )

    @abc.abstractmethod
    def create_message(self, role: MessageRole, content: str) -> ChatMessage:
        """
        Create a new ChatMessage with a text block.
        """

    @abc.abstractmethod
    def add_messages(
        self,
        messages: List[ChatMessage],
        new_messages: List[ChatMessage],
        index: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        Insert messages into a list at the given index.
        """

    @abc.abstractmethod
    def dump_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Convert messages into a serializable format.
        """

    @abc.abstractmethod
    def load_messages(self, data: List[Dict[str, Any]]) -> List[ChatMessage]:
        """
        Reconstruct messages from their dict representations.
        """

    # Adapter layer
    @abc.abstractmethod
    def to_framework_messages(self, messages: List[ChatMessage]) -> List[Any]:
        """
        Code in specific framework message type.
        """

    @abc.abstractmethod
    def from_framework_messages(self, messages: List[Any]) -> List[ChatMessage]:
        """
        Decode in specific framework message type.
        """

class SharedLogicMessageManager:
    """
    Shared reusable logic for message handling methods.
    To be used by concrete implementations like LangChain or LlamaIndex.
    """

    def __init__(self, config: dict) -> None:
        self.config = BaseMessageManager.Config(**config)
        self.result = BaseMessageManager.Result()

    @message_error_handler("Error creating message")
    def create_message(self, role: MessageRole, content: str) -> BaseMessageManager.Result:
        """
        Create a single ChatMessage with a text block.

        :param role: Role of the message (e.g., user, assistant, system).
        :param content: Text content of the message.
        :return: Result object with a single ChatMessage stored in `message` field.
        """
        if not isinstance(role, MessageRole):
            raise ValueError(f"Invalid role: {role}")
        msg = ChatMessage(role=role, blocks=[TextBlock(text=content)])
        self.result.status = "success"
        self.result.messages = [msg]
        return self.result

    @message_error_handler("Error adding message")
    def add_messages(
            self,
            messages: List[ChatMessage],
            new_messages: List[ChatMessage],
            index: Optional[int] = None
     ) -> BaseMessageManager.Result:
        """
        Insert new ChatMessages into an existing list of messages at a given index.

        :param messages: The original list of ChatMessages.
        :param new_messages: The ChatMessages to be inserted.
        :param index: Position to insert at (default: append to end).
        :return: Result object with the updated list stored in `messages`.
        """
        if index is None:
            combined = messages + new_messages
        else:
            combined = messages[:index] + new_messages + messages[index:]
        self.result.status = "success"
        self.result.messages = combined
        return self.result

    @message_error_handler("Error dumping message")
    def dump_messages(self, messages: List[ChatMessage]) -> BaseMessageManager.Result:
        """
        Serialize a list of ChatMessages into dictionaries suitable for storage or transmission.

        :param messages: List of ChatMessage objects to serialize.
        :return: Result object with the serialized output stored in `data`.
        """
        serialized = [msg.to_dict() for msg in messages]
        self.result.status = "success"
        self.result.messages = [serialized]
        return self.result

    @message_error_handler("Error loading message")
    def load_messages(self, data: List[Dict[str, Any]]) -> BaseMessageManager.Result:
        """
        Deserialize a list of message dictionaries back into ChatMessage objects.

        :param data: List of dicts representing serialized ChatMessages.
        :return: Result object with reconstructed ChatMessages in `messages`.
        """
        messages = [
            ChatMessage(
                id=msg.get("id"),
                timestamp=msg.get("timestamp"),
                role=MessageRole(msg["role"]),
                blocks=[TextBlock(**block) for block in msg.get("blocks", [])],
                metadata=msg.get("metadata", {})
            ) for msg in data
        ]
        self.result.status = "success"
        self.result.messages = messages
        return self.result
