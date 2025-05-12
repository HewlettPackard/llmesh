#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataStorage Module

This module defines the DataStorage class and associated class for 
managing different storage (e.g. Chroma dB, ...) 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.rag.data_storages.chroma.collection import (
    ChromaCollectionDataStorage)
from src.lib.services.rag.data_storages.qdrant.collection import (
    QdrantCollectionDataStorage)
from src.lib.services.rag.data_storages.milvus.collection import (
    MilvusCollectionDataStorage)


class DataStorage:  # pylint: disable=R0903
    """
    A section parser that uses a factory pattern to return
    the Data Storage
    """

    _storages: Dict[str, Type] = {
        'ChromaCollection': ChromaCollectionDataStorage,
        'QdrantCollection': QdrantCollectionDataStorage,
        'MilvusCollection': MilvusCollectionDataStorage,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return Data Storage
        
        :param config: Configuration dictionary containing the type of storage.
        :return: An instance of the selected data storage.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        storage_type = config.get('type')
        if not storage_type:
            raise ValueError("Configuration must include 'type'.")
        storage_class = DataStorage._storages.get(storage_type)
        if not storage_class:
            raise ValueError(f"Unsupported extractor type: {storage_type}")
        return storage_class(config)
