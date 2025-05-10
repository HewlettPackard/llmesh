#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Messages Manager Module

This module defines the Message Manager class and associated factory class for 
managing the messages formatting. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.chat.message_managers.langchain.prompts import (
    LangChainPromptsMessageManager)


class MessageManager:  # pylint: disable=R0903
    """
    A factory class to create Messages Manager objects with the selected services.
    """

    _messages: Dict[str, Type] = {
        'LangChainPrompts': LangChainPromptsMessageManager,
    }

    @staticmethod
    def create(config:dict) -> Any:
        """
        Create and return a message manager object based on the provided configuration.

        :param config: Dictionary containing configuration for message manager.
        :return: Message manager object
        :raises ValueError: If 'type' is not in config or unsupported type is provided.
        """
        message_type = config.get('type')
        if not message_type:
            raise ValueError("Configuration must include 'type'.")
        message_class = MessageManager._messages.get(message_type)
        if not message_class:
            raise ValueError(f"Unsupported prompt message manager type: {message_type}")
        return message_class(config)
