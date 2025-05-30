#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the LLamaIndexChatMessageManager implementation.
It includes both standard and corner case scenarios to ensure message creation,
insertion, serialization, and adapter conversion are robust and reliable.
"""

import os
from types import SimpleNamespace
import pytest
from llama_index.core.llms import ChatMessage as LlamaChatMessage
from src.lib.services.chat.message_managers.llamaindex.chat import LlamaIndexChatMessageManager
from src.lib.services.chat.message_managers.message import ChatMessage, MessageRole


@pytest.fixture
def llamaindex_config():
    """
    Fixture for LlamaIndexChatMessageManager configuration
    """
    return {"type": "LlamaIndex"}


@pytest.fixture
def manager(llamaindex_config):  # pylint: disable=W0621
    """
    Fixture for creating an instance of LlamaIndexChatMessageManager
    """
    return LlamaIndexChatMessageManager(llamaindex_config)


def test_create_message(manager):  # pylint: disable=W0621
    """
    Test creating a message from role and content.
    """
    result = manager.create_message(MessageRole.USER, "Hello")
    assert result.status == "success"
    assert result.messages[0].role == MessageRole.USER
    assert result.messages[0].to_text() == "Hello"


def test_add_messages(manager):  # pylint: disable=W0621
    """
    Test adding messages to a list at different positions.
    """
    msg1 = ChatMessage(role=MessageRole.USER, blocks=[])
    msg2 = ChatMessage(role=MessageRole.ASSISTANT, blocks=[])
    result = manager.add_messages([msg1], [msg2], index=0)
    assert result.status == "success"
    assert result.messages[0].role == MessageRole.ASSISTANT
    assert len(result.messages) == 2


def test_dump_and_load_messages(manager):  # pylint: disable=W0621
    """
    Test dumping messages to dicts and loading them back.
    """
    chat_msg = ChatMessage(role=MessageRole.USER, blocks=[])
    dump_result = manager.dump_messages([chat_msg])
    assert dump_result.status == "success"

    load_result = manager.load_messages(dump_result.messages[0])
    assert load_result.status == "success"
    assert load_result.messages[0].role == MessageRole.USER


def test_to_framework_messages(manager):  # pylint: disable=W0621
    """
    Test conversion of internal messages to LlamaIndex ChatMessage.
    """
    chat_msg = ChatMessage(role=MessageRole.USER, blocks=[])
    result = manager.to_framework_messages([chat_msg])
    assert result.status == "success"
    assert isinstance(result.messages, list)
    assert isinstance(result.messages[0], LlamaChatMessage)


def test_from_framework_messages(manager):  # pylint: disable=W0621
    """
    Test conversion from LlamaIndex ChatMessage to internal format.
    """
    llama_msg = LlamaChatMessage(role="user", content="Hi!")
    result = manager.from_framework_messages([llama_msg])
    assert result.status == "success"
    assert isinstance(result.messages[0], ChatMessage)
    assert result.messages[0].role == MessageRole.USER
    assert result.messages[0].to_text() == "Hi!"


def test_to_framework_messages_invalid_type(manager):  # pylint: disable=W0621
    """
    Test passing an invalid type to to_framework_messages.
    """
    result = manager.to_framework_messages(["not_a_message"])
    assert result.status == "failure"
    assert "Invalid message type" in result.error_message


def test_from_framework_messages_unknown_role(manager):  # pylint: disable=W0621
    """
    Test fallback/default role handling when LlamaIndex role is unknown.
    """
    unknown_msg = SimpleNamespace(role="alien", content="??")
    result = manager.from_framework_messages([unknown_msg])
    assert result.status == "success"
    assert result.messages[0].role == MessageRole.USER


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
