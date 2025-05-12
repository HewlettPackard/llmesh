#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module re-exports key functionalities related to RAG handling
within the lib. It simplifies the import for clients 
of the lib package.

The package name 'athon' is a shorthand for 'agentic-python', reflecting
its focus on building and managing agentic behaviors in Python-based systems.
"""

from src.lib.services.rag.data_extractor import DataExtractor
from src.lib.services.rag.data_transformer import DataTransformer
from src.lib.services.rag.data_storage import DataStorage
from src.lib.services.rag.data_loader import DataLoader
from src.lib.services.rag.data_retriever import DataRetriever


__all__ = [
    'DataExtractor',
    'DataTransformer',
    'DataStorage',
    'DataLoader',
    'DataRetriever'
]
