#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataLoader Module

This module defines the DataLoader class and associated class for 
managing different storage (e.g. Chroma dB, ...) 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.rag.data_loaders.chroma.sentences import (
    ChromaForSentenceDataLoader)
from src.lib.services.rag.data_loaders.qdrant.sentences import (
    QdrantForSentenceDataLoader)
from src.lib.services.rag.data_loaders.milvus.sentences import (
    MilvusForSentenceDataLoader)


class DataLoader:  # pylint: disable=R0903
    """
    A section parser that uses a factory pattern to return
    the Data Loader
    """

    _loaders: Dict[str, Type] = {
        'ChromaForSentences': ChromaForSentenceDataLoader,
        'QdrantForSentences': QdrantForSentenceDataLoader,
        'MilvusForSentences': MilvusForSentenceDataLoader,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return Data Loader
        
        :param config: Configuration dictionary containing the type of loader.
        :return: An instance of the selected data loader.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        loader_type = config.get('type')
        if not loader_type:
            raise ValueError("Configuration must include 'type'.")
        loader_class = DataLoader._loaders.get(loader_type)
        if not loader_class:
            raise ValueError(f"Unsupported extractor type: {loader_type}")
        return loader_class(config)
