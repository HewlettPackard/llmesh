#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manage chat history messages

This script handles the string to dict conversion in case of 
LangChain memory chat messages.
"""

import json
from langchain_core.messages import (
    HumanMessage, SystemMessage, AIMessage, FunctionMessage, ToolMessage)
from src.lib.core.log import Logger
from src.lib.services.chat.message_managers.base import BaseMessageManager


logger = Logger().get_logger()


class LangChainPromptsMessageManager(BaseMessageManager):
    """
    Message Formatter class to manage prompts.
    """

    def __init__(self, config: dict) -> None:
        """
        Initialize the formatter with the given configuration.

        :param config: Configuration dictionary for the formatter.
        """
        self.config = LangChainPromptsMessageManager.Config(**config)
        self.result = LangChainPromptsMessageManager.Result()

    def convert_to_messages(self, prompts_dict: dict) -> 'LangChainPromptsMessageManager.Result':
        """
        Convert a dictionary into an array of prompts.

        :param prompts_dict: Dictionary containing the prompts data.
        :return: Result object containing the status and converted prompts.
        """
        try:
            self.result.status = "success"
            if self.config.json_convert:
                messages_dict = json.loads(prompts_dict[self.config.memory_key])
                self.result.prompts = {
                    self.config.memory_key: self._calculate_to_messages(messages_dict),
                }
                if "input" in prompts_dict:
                    self.result.prompts["input"] = prompts_dict["input"]
            else:
                messages_dict = prompts_dict
                self.result.prompts = self._calculate_to_messages(messages_dict)
            logger.debug("Prompts converted to Langchain messages.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while loading the prompts: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _calculate_to_messages(self, prompts_dict: dict) -> list:
        """
        Convert a dictionary of messages into Langchain message objects.

        :param prompts_dict: Dictionary containing the messages.
        :return: List of message objects.
        """
        prompts = []
        for message in prompts_dict:
            message_type = message['type']
            content = message['content']
            if message_type == 'SystemMessage':
                prompts.append(SystemMessage(content=content))
            elif message_type == 'HumanMessage':
                prompts.append(HumanMessage(content=content))
            elif message_type == 'AIMessage':
                prompts.append(AIMessage(content=content))
            elif message_type == 'FunctionMessage':
                prompts.append(FunctionMessage(content=content))
            elif message_type == 'ToolMessage':
                prompts.append(ToolMessage(content=content))
            else:
                logger.warning(f"Message type '{message_type}' not supported")
        return prompts

    def convert_to_strings(self, prompts: list) -> 'LangChainPromptsMessageManager.Result':
        """
        Convert each message to a dictionary with a type field.

        :param prompts: List of message objects.
        :return: Result object containing the status and dictionary of prompts.
        """
        try:
            self.result.status = "success"
            if self.config.json_convert:
                messages = self._calculate_dict(prompts[self.config.memory_key])
                prompts[self.config.memory_key] = json.dumps(messages)
                prompts_dict = prompts
            else:
                prompts_dict = self._calculate_dict(prompts)
            self.result.prompts = prompts_dict
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while dumping the prompts: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _calculate_dict(self, messages: list) -> list:
        """
        Convert a list of message objects to a list of dictionaries.

        :param messages: List of message objects.
        :return: List of dictionaries representing the messages.
        """
        return [
            {
                'type': message.__class__.__name__,
                'content': message.content
            } for message in messages
        ]
