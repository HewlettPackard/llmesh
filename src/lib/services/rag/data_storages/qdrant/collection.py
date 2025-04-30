#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Qdrant Collection Data Storage

This module provides a strategy to manage Qdrant dB collections, allowing for the retrieval
or creation of collections by name.
"""

from typing import Dict, Any, Optional
from pydantic import Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.lib.services.rag.data_storages.base import BaseDataStorage
from src.lib.core.log import Logger


logger = Logger().get_logger()


class QdrantCollectionDataStorage(BaseDataStorage):  # pylint: disable=R0903
    """
    Strategy for managing Qdrant dB collections.
    """

    _collections = {}  # Cache to store collections based on path and collection name

    class Config(BaseDataStorage.Config):
        """
        Configuration for QdrantCollectionDataStorage.
        """
        url: str = Field(
            ...,
            description="URL to the database."
        )
        vector_size: Optional[int] = Field(
            default=1536,
            description="Dimension of vector embeddings"
        )
        distance: Optional[str] = Field(
            default=Distance.COSINE,
            description="Distance for vector search, other options include EUCLID, DOT"
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the QdrantCollectionDataStorage with the given configuration.

        :param config: Dictionary containing configuration values.
        """
        self.config = QdrantCollectionDataStorage.Config(**config)
        self.result = QdrantCollectionDataStorage.Result()
        collection_key = (self.config.url, self.config.collection)
        if collection_key not in QdrantCollectionDataStorage._collections or self.config.reset:
            QdrantCollectionDataStorage._collections[collection_key] = self._create_collection()
        self._qdrant_collection = QdrantCollectionDataStorage._collections[collection_key]

    def _create_collection(self) -> Dict:
        """
        Create or retrieve a QdrantDb collection.

        :return: The QdrantDb collection name.
        """
        qdrant_client = QdrantClient(url=self.config.url)
        logger.debug(
            f"Attempting to get or create QdrantDb collection '{self.config.collection}'.")
        collection_name = self._get_or_create_collection(qdrant_client)
        if self.config.reset:
            logger.debug(f"Resetting QdrantDb collection '{self.config.collection}'.")
            qdrant_client.delete_collection(collection_name=self.config.collection)
            logger.debug(f"Re-creating QdrantDb collection '{self.config.collection}'.")
            collection_name = self._get_or_create_collection(qdrant_client)
        collection = {
            "client": qdrant_client,
            "name": collection_name,
        }
        return collection

    def _get_or_create_collection(
            self,
            qdrant_client: QdrantClient
        ) -> str:
        """
        Helper method to create or retrieve a collection from QdrantDb.

        :param qdrant_client: The QdrantClient instance.
        :return: The created or retrieved collection.
        """
        collection_name = self.config.collection
        vector_size = self.config.vector_size
        distance_metric = self.config.distance
        if not qdrant_client.collection_exists(collection_name):
            logger.debug(
                f"Creating QdrantDb collection '{collection_name}' with vector size {vector_size}")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance_metric)
            )
        else:
            logger.debug(f"Collection '{collection_name}' already exists in QdrantDb.")
        collection_info = qdrant_client.get_collection(collection_name)
        logger.debug(f"Collection info: {collection_info}")
        return collection_name

    def get_collection(self) -> 'QdrantCollectionDataStorage.Result':
        """
        Retrieve the Qdrant dB collection based on the current configuration.

        :return: Result object containing the collection name or error details.
        """
        try:
            self.result.status = "success"
            self.result.collection = self._qdrant_collection
            logger.debug("Successfully retrieved the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while retrieving the collection: {e}"
            logger.error(self.result.error_message)
        return self.result
