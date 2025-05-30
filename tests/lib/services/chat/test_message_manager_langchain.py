#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the LangChainChatMessageManager implementation.
It includes both standard and corner case scenarios to ensure message creation,
insertion, serialization, and adapter conversion are robust and reliable.
"""

import os
import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.lib.services.chat.message_managers.langchain.chat import LangChainChatMessageManager
from src.lib.services.chat.message_managers.message import ChatMessage, MessageRole, TextBlock


@pytest.fixture
def langchain_message_config():
    """
    Fixture to return a mock LangChain message manager configuration.
    """
    return {
        "type": "LangChain"
    }


@pytest.fixture
def manager(langchain_message_config):  # pylint: disable=W0621
    """
    Fixture to return a LangChainChatMessageManager instance.
    """
    return LangChainChatMessageManager(langchain_message_config)


def test_create_message(manager):  # pylint: disable=W0621
    """
    Test that create_message successfully returns a valid ChatMessage object.
    """
    result = manager.create_message(MessageRole.USER, "Hello")
    assert result.status == "success"
    assert len(result.messages) == 1
    assert isinstance(result.messages[0], ChatMessage)


def test_add_messages(manager):  # pylint: disable=W0621
    """
    Test that add_messages correctly inserts new messages at the given index.
    """
    msg1 = ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Hi")])
    msg2 = ChatMessage(role=MessageRole.ASSISTANT, blocks=[TextBlock(text="Hello")])
    result = manager.add_messages([msg1], [msg2], index=1)
    assert result.status == "success"
    assert result.messages[1].role == MessageRole.ASSISTANT


def test_dump_and_load_messages(manager):  # pylint: disable=W0621
    """
    Test that dump_messages serializes correctly and load_messages reconstructs properly.
    """
    msg = ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Dump me")])
    dumped = manager.dump_messages([msg])
    loaded = manager.load_messages(dumped.messages[0])
    assert loaded.status == "success"
    assert loaded.messages[0].blocks[0].text == "Dump me"


def test_to_framework_messages(manager):  # pylint: disable=W0621
    """
    Test that to_framework_messages returns LangChain-compatible messages.
    """
    msg = ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="User text")])
    converted = manager.to_framework_messages([msg])
    assert converted[0].content == "User text"


def test_from_framework_messages(manager):  # pylint: disable=W0621
    """
    Test that from_framework_messages returns valid internal ChatMessage objects.
    """
    lc_messages = [
        HumanMessage(content="User"),
        AIMessage(content="Bot"),
        SystemMessage(content="System")
    ]
    internal = manager.from_framework_messages(lc_messages)
    assert len(internal) == 3
    assert internal[0].role == MessageRole.USER


def test_create_message_invalid_role(manager):  # pylint: disable=W0621
    """
    Test that create_message fails gracefully when an invalid role is passed.
    """
    result = manager.create_message("invalid", "text")  # type: ignore
    assert result.status == "failure"
    assert "invalid" in result.error_message


def test_add_messages_invalid_index(manager):  # pylint: disable=W0621
    """
    Test that add_messages fails with a non-integer index value.
    """
    msg = ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="msg")])
    result = manager.add_messages([msg], [msg], index="bad-index")  # type: ignore
    assert result.status == "failure"


def test_add_messages_none_lists(manager):  # pylint: disable=W0621
    """
    Test that add_messages fails when None is passed instead of a list.
    """
    result = manager.add_messages(None, None)  # type: ignore
    assert result.status == "failure"


def test_dump_messages_with_invalid_message(manager):  # pylint: disable=W0621
    """
    Test that dump_messages fails when given a non-ChatMessage object.
    """
    result = manager.dump_messages(["not-a-message"])  # type: ignore
    assert result.status == "failure"


def test_load_messages_with_invalid_dict(manager):  # pylint: disable=W0621
    """
    Test that load_messages fails when given improperly formatted dictionaries.
    """
    result = manager.load_messages([{"broken": "data"}])
    assert result.status == "failure"


def test_to_framework_messages_invalid_type(manager):  # pylint: disable=W0621
    """
    Test that to_framework_messages fails safely on non-ChatMessage inputs.
    """
    result = manager.to_framework_messages(["bad-type"])  # type: ignore
    assert isinstance(result, list)
    assert len(result) == 0


def test_from_framework_messages_unknown_type(manager):  # pylint: disable=W0621
    """
    Test that from_framework_messages returns fallback messages on unrecognized types.
    """
    class FakeMessage:
        "fake class"
        content = "???"
    result = manager.from_framework_messages([FakeMessage()])
    assert isinstance(result, list)
    assert result[0].role == MessageRole.USER


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
