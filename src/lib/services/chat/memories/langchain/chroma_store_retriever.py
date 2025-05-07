#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain Vector Store Memory

This module allow to
- initialize and return the LangChain vector store retriever memory
"""

import re
from typing import Any, List, Union, Dict
from pydantic import Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import VectorStoreRetrieverMemory
from src.lib.core.log import Logger
from src.lib.services.chat.memories.base import BaseChatMemory


logger = Logger().get_logger()


class CustomVectorStoreRetrieverMemory(VectorStoreRetrieverMemory):
    """
    Overwrite class to return Base Messages
    """

    def load_memory_variables(
        self, inputs: Dict[str, Any]
    ) -> Dict[str, Union[List[BaseMessage], str]]:
        """
        Overwrite Load Memory casting in base message

        :param inputs: Dictionary of input variables.
        :return: Dictionary with casted memory variables.
        """
        try:
            # Call the original method to get the result
            original_result = super().load_memory_variables(inputs)
            # Get the result from the original method using the memory key
            result = original_result[self.memory_key]
            # Cast the result to BaseMessage
            if isinstance(result, list):
                casted_result = self._process_documents(result)
            elif isinstance(result, str):
                casted_result = self._convert_string_to_messages(result)
            else:
                logger.error("Unsupported result type")
                raise ValueError("Unsupported result type")
            return {self.memory_key: casted_result}
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"An error occurred while loading memory variables: {e}")
            return None

    def _process_documents(self, result: List[Document]) -> List[BaseMessage]:
        """
        Process a list of Document objects and convert them to BaseMessage objects.

        :param result: List of Document objects.
        :return: List of BaseMessage objects.
        """
        messages = []
        for doc in result:
            if isinstance(doc, Document):
                messages.extend(self._convert_string_to_messages(doc.page_content))
        return messages

    def _convert_string_to_messages(self, input_str: str) -> List[BaseMessage]:
        """
        Convert a string to a list of BaseMessage objects.

        :param input_str: Input string to be converted.
        :return: List of BaseMessage objects.
        """
        # Define regex patterns for input and output
        input_pattern = re.compile(r'input:\s*(.*)')
        output_pattern = re.compile(r'output:\s*(.*)')
        # Extract input and output messages
        input_match = input_pattern.search(input_str)
        output_match = output_pattern.search(input_str)
        if input_match and output_match:
            input_message = input_match.group(1).strip()
            output_message = output_match.group(1).strip()
            return [
                HumanMessage(content=input_message, additional_kwargs={}),
                AIMessage(content=output_message, additional_kwargs={})
            ]
        logger.error(
            "The input string does not contain the expected " 
            "'input' and 'output' patterns."
        )
        raise ValueError(
            "The input string does not contain the "
            "expected 'input' and 'output' patterns."
        )


class LangChainChromaStoreMemory(BaseChatMemory):
    """
    Class LangChain Chroma Vector Store Memory Model
    """

    class Config(BaseChatMemory.Config):
        """
        Arguments of the Chat Memory class
        """
        persist_directory: str = Field(
            ...,
            description="Folder containing the dB"
        )
        collection_name: str = Field(
            ...,
            description="Name of the dB collection"
        )
        k: int = Field(
            default=1,
            description="Name of the dB collection"
        )

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the memory with the given configuration.

        :param config: Configuration dictionary for the memory.
        """
        self.config = LangChainChromaStoreMemory.Config(**config)
        self.result = LangChainChromaStoreMemory.Result()
        self.retriever = self._init_retriever()
        self.memory = self._init_memory()

    def _init_retriever(self) -> VectorStoreRetriever:
        """
        Initialize and return the vector store retriever.

        :return: VectorStoreRetriever instance.
        """
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory = self.config.persist_directory,
            embedding_function=embeddings,
            collection_name = self.config.collection_name)
        return vectorstore.as_retriever(
            search_kwargs={"k":self.config.k})

    def _init_memory(self) -> CustomVectorStoreRetrieverMemory:
        """
        Initialize and return the memory.

        :return: CustomVectorStoreRetrieverMemory instance.
        """
        logger.debug("Selected LangChain Buffer Memory")
        return CustomVectorStoreRetrieverMemory(
            retriever=self.retriever,
            return_docs=True,
            memory_key = self.config.memory_key)

    def get_memory(self) -> 'LangChainChromaStoreMemory.Result':
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

    def clear(self) -> 'LangChainChromaStoreMemory.Result':
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
