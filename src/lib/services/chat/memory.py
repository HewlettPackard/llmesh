#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chat Memory Module

This module defines the ChatMemory class and associated class for 
managing different LLM chat memory. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.chat.memories.langchain.buffer import (
    LangChainBufferMemory)
from src.lib.services.chat.memories.langchain.buffer_window import (
    LangChainBufferWindowMemory)
from src.lib.services.chat.memories.langchain.summary import (
    LangChainSummaryMemory)
from src.lib.services.chat.memories.langchain.chroma_store_retriever import (
    LangChainChromaStoreMemory)
from src.lib.services.chat.memories.langchain.custom_remote import (
    LangChainRemoteMemory)
from src.lib.services.chat.memories.llamaindex.buffer import (
    LlamaIndexBufferMemory)


class ChatMemory:  # pylint: disable=R0903
    """
    A chat model class that uses a factory pattern to return
    the selected chat memory
    """

    _memories: Dict[str, Type] = {
        'LangChainBuffer': LangChainBufferMemory,
        'LangChainBufferWindow': LangChainBufferWindowMemory,
        'LangChainSummary': LangChainSummaryMemory,
        'LangChainChromaStore': LangChainChromaStoreMemory,
        'LangChainRemote': LangChainRemoteMemory,
        'LlamaIndexBuffer': LlamaIndexBufferMemory,
    }

    @staticmethod
    def create(config: Dict[str, Any]) -> object:
        """
        Return the memory class.

        :param config: Configuration dictionary containing the type of memory.
        :return: An instance of the selected memory.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        memory_type = config.get('type')
        if not memory_type:
            raise ValueError("Configuration must include 'type'.")
        memory_class = ChatMemory._memories.get(memory_type)
        if not memory_class:
            raise ValueError(f"Unsupported extractor type: {memory_type}")
        return memory_class(config)
