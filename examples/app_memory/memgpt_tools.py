#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MemGPT Tools

This module implements the tools for saving and retrieving memories

Note: Derived by Lang-MemGPT (repo: https://github.com/langchain-ai/lang-memgpt)
"""

import uuid
from datetime import datetime, timezone
from typing import Any, List
from langchain_core.tools import tool
from self_serve_platform.chat.memory import ChatMemory
from self_serve_platform.rag.data_storage import DataStorage
from self_serve_platform.rag.data_loader import DataLoader
from self_serve_platform.rag.data_retriever import DataRetriever
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger


# Parse command-line arguments and start the application
PATH = 'examples/app_memory/'
CONFIG = Config(PATH+'config.yaml').get_settings()

MEMORY_CONFIG = CONFIG["memory"]["core"]
STORAGE_CONFIG = CONFIG["memory"]["recall"]["storage"]
LOADER_CONFIG = CONFIG["memory"]["recall"]["loader"]
RETRIEVER_CONFIG = CONFIG["memory"]["recall"]["retriever"]

# Create Logger
logger = Logger().configure(CONFIG["logger"]).get_logger()


def _get_collection():
    data_storage= DataStorage.create(STORAGE_CONFIG)
    result = data_storage.get_collection()
    return result.collection

def _get_memory():
    chat_memory = ChatMemory.create(MEMORY_CONFIG)
    result = chat_memory.get_memory()
    return result.memory

recall_collection = _get_collection()
core_memory = _get_memory()


@tool
async def save_recall_memory(memory: str) -> str:
    """Save a memory to the database for later semantic retrieval.

    Args:
        memory (str): The memory to be saved.

    Returns:
        str: The saved memory.
    """
    element = {
        "text": memory,
        "metadata": {
            "type": "recall",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(tz=timezone.utc),
        }
    }
    _load_element(recall_collection, element)
    return memory

def _load_element(collection, element):
    data_loader = DataLoader.create(LOADER_CONFIG)
    data_loader.insert(collection, [element])

@tool
def search_memory(query: str) -> list[str]:
    """Search for memories in the database based on semantic similarity.

    Args:
        query (str): The search query.

    Returns:
        list[str]: A list of relevant memories.
    """
    result = _retrieve_from_collection(recall_collection, query)
    if result.status == "success" and result.elements:
        return [item["text"] for item in result.elements]
    return []

def _retrieve_from_collection(collection, query):
    data_retriever = DataRetriever.create(RETRIEVER_CONFIG)
    result = data_retriever.select(collection, query)
    return result


def fetch_core_memories() -> List[Any]:
    """Fetch core memories for a specific user.

    Returns:
        List[Any]: The list of core memories.
    """
    memories = core_memory.load_memory_variables({})
    return memories[MEMORY_CONFIG["memory_key"]]


@tool
def save_core_memory(memory: str) -> str:
    """Store a core memory in the database.

    Args:
        memory (str): The memory to store.

    Returns:
        str: A confirmation message.
    """
    #TODO: wron input is human when output is assistant
    old_memories = core_memory.load_memory_variables({})
    core_memory.save_context(memory, old_memories)
    return "Memory stored."
