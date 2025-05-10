#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chroma Collection Data Storage

This module provides a strategy to manage Chroma dB collections, allowing for the retrieval
or creation of collections by name.
"""

from typing import Optional, Dict, Any
from pydantic import Field
from chromadb import PersistentClient
from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import (
    SentenceTransformerEmbeddingFunction)
from src.lib.services.rag.data_storages.base import BaseDataStorage
from src.lib.core.log import Logger


logger = Logger().get_logger()


class ChromaCollectionDataStorage(BaseDataStorage):  # pylint: disable=R0903
    """
    Strategy for managing Chroma dB collections.
    """

    _collections = {}  # Cache to store collections based on path and collection name

    class Config(BaseDataStorage.Config):
        """
        Configuration for ChromaCollectionDataStorage.
        """
        path: str = Field(
            ...,
            description="Path to the database."
        )
        metadata: Optional[Dict[str, str]] = Field(
            default={"hnsw:space": "cosine"},
            description="Metadata for configuring the collection."
        )
        embeddings_model: Optional[str] = Field(
            default="all-MiniLM-L6-v2",
            description="Name of the embeddings model."
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ChromaCollectionDataStorage with the given configuration.

        :param config: Dictionary containing configuration values.
        """
        self.config = ChromaCollectionDataStorage.Config(**config)
        self.result = ChromaCollectionDataStorage.Result()
        collection_key = (self.config.path, self.config.collection)
        if collection_key not in ChromaCollectionDataStorage._collections or self.config.reset:
            ChromaCollectionDataStorage._collections[collection_key] = self._create_collection()
        self._chroma_collection = ChromaCollectionDataStorage._collections[collection_key]

    def _create_collection(self) -> 'PersistentClient.Collection':
        """
        Create or retrieve a Chroma dB collection.

        :return: The Chroma dB collection.
        """
        chroma_client = PersistentClient(path=self.config.path)
        logger.debug(
            f"Attempting to get or create Chroma dB collection '{self.config.collection}'.")
        collection = self._get_or_create_collection(chroma_client)
        if self.config.reset:
            logger.debug(f"Resetting Chroma dB collection '{self.config.collection}'.")
            chroma_client.delete_collection(name=self.config.collection)
            logger.debug(f"Re-creating Chroma dB collection '{self.config.collection}'.")
            collection = self._get_or_create_collection(chroma_client)
        return collection

    def _get_or_create_collection(
            self,
            chroma_client: PersistentClient
        ) -> 'PersistentClient.Collection':
        """
        Helper method to create or retrieve a collection from Chroma dB.

        :param chroma_client: The Chroma PersistentClient instance.
        :return: The created or retrieved collection.
        """
        collection_args = {
            "name": self.config.collection,
            "metadata": self.config.metadata,
        }
        if self.config.embeddings_model:
            embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=self.config.embeddings_model
            )
            collection_args["embedding_function"] = embedding_function
        logger.debug(f"Creating or retrieving collection with arguments: {collection_args}")
        return chroma_client.get_or_create_collection(**collection_args)

    def get_collection(self) -> 'ChromaCollectionDataStorage.Result':
        """
        Retrieve the Chroma dB collection based on the current configuration.

        :return: Result object containing the collection or error details.
        """
        try:
            self.result.status = "success"
            self.result.collection = self._chroma_collection
            logger.debug("Successfully retrieved the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while retrieving the collection: {e}"
            logger.error(self.result.error_message)
        return self.result
