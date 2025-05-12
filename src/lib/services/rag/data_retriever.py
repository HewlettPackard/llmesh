#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataRetriever Module

This module defines the DataRetriever class and associated class for 
managing different storage (e.g. Chroma dB, ...) 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.rag.data_retrievers.chroma.sentences import (
    ChromaForSentenceDataRetriever)
from src.lib.services.rag.data_retrievers.qdrant.sentences import (
    QdrantForSentenceDataRetriever)
from src.lib.services.rag.data_retrievers.milvus.sentences import (
    MilvusForSentenceDataRetriever)


class DataRetriever:  # pylint: disable=R0903
    """
    A section parser that uses a factory pattern to return
    the Data Retriever
    """

    _retrievers: Dict[str, Type] = {
        'ChromaForSentences': ChromaForSentenceDataRetriever,
        'QdrantForSentences': QdrantForSentenceDataRetriever,
        'MilvusForSentences': MilvusForSentenceDataRetriever,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return Data Retriever
        
        :param config: Configuration dictionary containing the type of retriever.
        :return: An instance of the selected data retriever.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        retriever_type = config.get('type')
        if not retriever_type:
            raise ValueError("Configuration must include 'type'.")
        retriever_class = DataRetriever._retrievers.get(retriever_type)
        if not retriever_class:
            raise ValueError(f"Unsupported extractor type: {retriever_type}")
        return retriever_class(config)
