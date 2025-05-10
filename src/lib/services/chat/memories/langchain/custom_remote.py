#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Remote Memory

This module allows to:
- initialize and return a memory that can connect with a remote webapp
"""

from typing import Optional, Any, Dict
from pydantic import Field
import requests
from langchain.schema import BaseMemory
from src.lib.core.log import Logger
from src.lib.services.chat.message_manager import MessageManager
from src.lib.services.chat.memories.base import BaseChatMemory


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
        self.message_manager = self._init_message_manager()

    def _init_message_manager(self) -> MessageManager:
        """
        Initialize and return the MessageManager.

        :return: MessageManager instance.
        """
        messages_config = {
            "type": "LangChainPrompts",
            "json_convert": True,
            "memory_key": self.config.get("memory_key", "")
        }
        return MessageManager.create(messages_config)

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
            result = self.message_manager.convert_to_messages(response.json())
            if result.status == "success":
                return result.prompts
            logger.error(result.error_message)
        return None

    def save_context(self, inputs: Any, outputs: Any) -> None:
        """
        Store data to the remote memory endpoint.

        :param inputs: Inputs to save.
        :param outputs: Outputs to save.
        """
        url = self._get_endpoint_url('store')
        result = self.message_manager.convert_to_strings(inputs)
        if result.status == "success":
            data = {
                'inputs': result.prompts,
                'outputs': outputs
            }
            self._post_request(url, data)
        else:
            logger.error(result.error_message)

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

    def get_memory(self) -> 'LangChainRemoteMemory.Result':
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

    def clear(self) -> 'LangChainRemoteMemory.Result':
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
