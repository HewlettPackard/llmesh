#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Remote Memory

This module allows to:
- initialize and return a memory that can connect with a remote webapp
"""

from __future__ import annotations
from typing import Optional, Any, Dict
import json
from pydantic import Field
import requests
from langchain_core.messages import (
    BaseMessage, HumanMessage, SystemMessage,
    AIMessage, FunctionMessage, ToolMessage
)
from langchain.schema import BaseMemory
from src.lib.services.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory
from src.lib.services.chat.memories.error_handler import memory_error_handler


logger = Logger().get_logger()


class CustomLangChainRemoteMemory(BaseMemory):
    """
    Custom Remote Memory Class.
    """

    config: Dict[str, Any] = Field(default_factory=dict)
    message_manager: Any

    def __init__(self, config: Dict[str, Any], **kwargs) -> None:
        """
        Initialize the CustomLangChainRemoteMemory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        kwargs["message_manager"] = Any
        super().__init__(**kwargs)
        self.config = config

    def load_memory_variables(self, inputs: Any) -> Optional[Any]:
        """
        Load data from the remote memory endpoint.

        :param inputs: Inputs to load from memory.
        :return: Loaded memory data.
        """
        url = self._get_endpoint_url('load')
        data = {'inputs': inputs}
        response = self._post_request(url, data)
        if response:
            result = self.convert_to_messages(response.json())
            if result["status"] == "success":
                return result["messages"]
            logger.error(result["error_message"])
        return None

    def save_context(self, inputs: Any, outputs: Any) -> None:
        """
        Store data to the remote memory endpoint.

        :param inputs: Inputs to save.
        :param outputs: Outputs to save.
        """
        url = self._get_endpoint_url('store')
        result = self.convert_to_strings(inputs)
        if result["status"] == "success":
            data = {
                'inputs': result["messages"],
                'outputs': outputs
            }
            self._post_request(url, data)
        else:
            logger.error(result["error_message"])

    def clear(self) -> None:
        """
        Clear data in the remote memory endpoint.
        """
        url = self._get_endpoint_url('clear')
        self._post_request(url)

    def _get_endpoint_url(self, endpoint: str) -> str:
        """
        Construct the full endpoint URL.

        :param endpoint: Endpoint path.
        :return: Full endpoint URL.
        """
        return f"{self.config.get('base_url')}/{endpoint}"

    def _post_request(
            self, url: str, data: Optional[Dict[str, Any]] = None
        ) -> Optional[requests.Response]:
        """
        Make a POST request to the given URL with the provided data.

        :param url: URL to make the POST request to.
        :param data: Data to include in the POST request.
        :return: Response object if the request was successful, None otherwise.
        """
        try:
            response = requests.post(
                url,
                json=data,
                verify=self.config.get('cert_verify', True),
                timeout=self.config.get('timeout', 10)
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
        return None

    def convert_to_messages(self, prompts_dict: dict) -> dict:
        """
        Convert a dictionary into an array of prompts.

        :param prompts_dict: Dictionary containing the prompts data.
        :return: Result object containing the status and converted prompts.
        """
        try:
            result = {}
            result["status"] = "success"
            result["messages"] = {}
            memory_key = self.config.get("memory_key", "")
            messages_dict = json.loads(prompts_dict[memory_key])
            result["messages"] = {
                memory_key: self._calculate_to_messages(messages_dict),
            }
            if "input" in prompts_dict:
                result["messages"]["input"] = prompts_dict["input"]
            logger.debug("Prompts converted to Langchain messages.")
        except Exception as e:  # pylint: disable=W0718
            result["status"] = "failure"
            result["error_message"] = f"An error occurred while loading the prompts: {e}"
            logger.error(result["error_message"])
        return result

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

    def convert_to_strings(self, prompts: list) -> dict:
        """
        Convert each message to a dictionary with a type field.

        :param prompts: List of message objects.
        :return: Result object containing the status and dictionary of prompts.
        """
        try:
            result = {}
            result["status"] = "success"
            result["messages"] = {}
            memory_key = self.config.get("memory_key", "")
            messages = self._calculate_dict(prompts[memory_key])
            prompts[memory_key] = json.dumps(messages)
            prompts_dict = prompts
            result["messages"] = prompts_dict
        except Exception as e:  # pylint: disable=W0718
            result["status"] = "failure"
            result["error_message"] = f"An error occurred while dumping the prompts: {e}"
            logger.error(result["error_message"])
        return result

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

    @property
    def memory_variables(self):
        """
        Implementing the abstract property from BaseMemory.
        :return: Dict representing the memory variables.
        """
        return {}


class LangChainRemoteMemory(BaseChatMemory):
    """
    Class for Remote Memory Model.
    """

    class Config(BaseChatMemory.Config):
        """
        Configuration for the Chat Memory class.
        """
        base_url: str = Field(
            ...,
            description="Endpoint of the remote app."
        )
        timeout: Optional[int] = Field(
            default=10,
            description="HTTP request timeout."
        )
        cert_verify: Optional[bool] = Field(
            default=True,
            description="HTTPS verification of the certificate."
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the memory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        self.config = LangChainRemoteMemory.Config(**config)
        self.result = LangChainRemoteMemory.Result()
        self.memory = self._init_memory()

    def _init_memory(self) -> CustomLangChainRemoteMemory:
        """
        Initialize and return the CustomLangChainRemoteMemory instance.

        :return: CustomLangChainRemoteMemory instance.
        """
        logger.debug("Selected LangChain Remote Memory")
        return CustomLangChainRemoteMemory(self.config.model_dump())

    def get_memory(self) -> LangChainRemoteMemory.Result:
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

    def clear(self) -> LangChainRemoteMemory.Result:
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
    def save_message(self, message: Any) -> LangChainRemoteMemory.Result:
        """
        Save a message pair (HumanMessage, AIMessage) to the remote memory via the API.

        :param message: A list or tuple of two messages (HumanMessage, AIMessage).
        :return: Result object containing the status of the save operation.
        """
        self.result.status = "success"
        # Validate the message structure
        if not (
            isinstance(message, (list, tuple)) and
            len(message) == 2 and
            isinstance(message[0], BaseMessage) and
            isinstance(message[1], BaseMessage)
        ):
            raise TypeError(
                "Remote memory expects a [HumanMessage, AIMessage] list/tuple."
            )
        human_msg, ai_msg = message
        # Convert inputs using message manager
        result = self.memory.convert_to_strings([human_msg])
        if result["status"] != "success":
            raise ValueError(result["error_message"] or "Failed to convert human message.")
        # Call remote save_context
        self.memory.save_context(result["messages"], ai_msg.content)
        logger.debug("Message pair saved to remote memory")
        return self.result

    @memory_error_handler("Error retrieving message")
    def get_messages(self, limit: Optional[int] = None) -> LangChainRemoteMemory.Result:
        """
        Retrieve messages from remote memory.
        :param limit: Optional max number of messages to return.
        :return: Result object containing a list of messages.
        """
        self.result.status = "success"
        messages = self.memory.load_memory_variables({}) or []
        if limit is not None:
            messages = messages[-limit:]
        self.result.messages = messages
        logger.debug(f"Retrieved {len(messages)} messages from remote memory")
        return self.result
