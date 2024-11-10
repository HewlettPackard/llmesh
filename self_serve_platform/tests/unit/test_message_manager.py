#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest file contains unit tests for the MessageManager factory class
and the LangChainPromptsMessageManager class. These tests ensure that the
factory method correctly creates instances of the message manager based on
the provided configuration and verify the functionality of the
LangChainPromptsMessageManager class for converting prompts between different formats.

"""

import json
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from self_serve_platform.chat.message_manager import MessageManager
from self_serve_platform.chat.message_managers.langchain_prompts import (
    LangChainPromptsMessageManager)


@pytest.fixture
def langchain_prompts_config():
    """
    Mockup configuration for LangChainPromptsMessageManager
    """
    return {
        "type": "LangChainPrompts",
        "json_convert": True,
        "memory_key": "chat_history"
    }


def test_message_manager_create_langchain_prompts(langchain_prompts_config):  # pylint: disable=W0621
    """
    Test the MessageManager factory to ensure it creates a LangChainPromptsMessageManager instance
    """
    manager = MessageManager.create(langchain_prompts_config)
    assert isinstance(manager, LangChainPromptsMessageManager)


def test_message_manager_create_invalid_type():
    """
    Test the MessageManager factory to ensure it raises a ValueError for unsupported types
    """
    config = {
        "type": "UnsupportedType"
    }
    with pytest.raises(
        ValueError, match="Unsupported prompt message manager type: UnsupportedType"):
        MessageManager.create(config)


@pytest.fixture
def langchain_prompts_message_manager(langchain_prompts_config):  # pylint: disable=W0621
    """
    Fixture for LangChainPromptsMessageManager instance
    """
    return LangChainPromptsMessageManager(langchain_prompts_config)


def test_convert_to_messages_success(langchain_prompts_message_manager):  # pylint: disable=W0621
    """
    Test the convert_to_messages method for successful conversion
    """
    prompts_dict = {
        "chat_history": json.dumps([
            {"type": "HumanMessage", "content": "Hello"},
            {"type": "AIMessage", "content": "Hi, how can I help you?"}
        ])
    }
    result = langchain_prompts_message_manager.convert_to_messages(prompts_dict)
    assert result.status == "success"
    assert len(result.prompts["chat_history"]) == 2
    assert isinstance(result.prompts["chat_history"][0], HumanMessage)
    assert isinstance(result.prompts["chat_history"][1], AIMessage)
    assert result.prompts["chat_history"][0].content == "Hello"
    assert result.prompts["chat_history"][1].content == "Hi, how can I help you?"


def test_convert_to_messages_failure(langchain_prompts_message_manager):  # pylint: disable=W0621
    """
    Test the convert_to_messages method for failure scenario
    """
    prompts_dict = {
        "chat_history": "invalid_json"
    }
    result = langchain_prompts_message_manager.convert_to_messages(prompts_dict)
    assert result.status == "failure"
    assert result.error_message is not None


def test_convert_to_strings_success(langchain_prompts_message_manager):  # pylint: disable=W0621
    """
    Test the convert_to_strings method for successful conversion
    """
    prompts = {
        "chat_history": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi, how can I help you?")
        ]
    }
    result = langchain_prompts_message_manager.convert_to_strings(prompts)
    assert result.status == "success"
    assert isinstance(result.prompts, dict)
    assert result.prompts["chat_history"] == (
        '[{"type": "HumanMessage", "content": "Hello"}, '
        '{"type": "AIMessage", "content": "Hi, how can I help you?"}]'
    )


def test_convert_to_strings_failure(langchain_prompts_message_manager):  # pylint: disable=W0621
    """
    Test the convert_to_strings method for failure scenario
    """
    prompts = "invalid_prompts"
    result = langchain_prompts_message_manager.convert_to_strings(prompts)
    assert result.status == "failure"
    assert result.error_message is not None


@pytest.fixture
def langchain_prompts_config_no_json():
    """
    Mockup configuration for LangChainPromptsMessageManager with json_convert=False
    """
    return {
        "type": "LangChainPrompts",
        "json_convert": False,
        "memory_key": "chat_history"
    }


@pytest.fixture
def langchain_prompts_message_manager_no_json(langchain_prompts_config_no_json):  # pylint: disable=W0621
    """
    Fixture for LangChainPromptsMessageManager instance with json_convert=False
    """
    return LangChainPromptsMessageManager(langchain_prompts_config_no_json)


def test_convert_to_messages_no_json_success(langchain_prompts_message_manager_no_json):  # pylint: disable=W0621
    """
    Test the convert_to_messages method for successful conversion with json_convert=False
    """
    prompts_dict = [
        {"type": "HumanMessage", "content": "Hello"},
        {"type": "AIMessage", "content": "Hi, how can I help you?"}
    ]
    result = langchain_prompts_message_manager_no_json.convert_to_messages(prompts_dict)
    assert result.status == "success"
    assert len(result.prompts) == 2
    assert isinstance(result.prompts[0], HumanMessage)
    assert isinstance(result.prompts[1], AIMessage)
    assert result.prompts[0].content == "Hello"
    assert result.prompts[1].content == "Hi, how can I help you?"


def test_convert_to_strings_no_json_success(langchain_prompts_message_manager_no_json):  # pylint: disable=W0621
    """
    Test the convert_to_strings method for successful conversion with json_convert=False
    """
    prompts = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi, how can I help you?")
    ]
    result = langchain_prompts_message_manager_no_json.convert_to_strings(prompts)
    assert result.status == "success"
    assert isinstance(result.prompts, list)
    assert result.prompts == [
        {"type": "HumanMessage", "content": "Hello"},
        {"type": "AIMessage", "content": "Hi, how can I help you?"}
    ]


if __name__ == "__main__":
    pytest.main([__file__, '-vv'])
