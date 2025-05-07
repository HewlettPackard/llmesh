#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Milvus Collection Data Storage

This module provides a strategy to manage Milvus dB collections, allowing for the retrieval
or creation of collections by name.
"""

from typing import Dict, Any, Optional
from pydantic import Field
from pymilvus import (
    MilvusClient,
    CollectionSchema,
    DataType,
    FieldSchema
)
from src.lib.services.rag.data_storages.base import BaseDataStorage
from src.lib.core.log import Logger


logger = Logger().get_logger()


class MilvusCollectionDataStorage(BaseDataStorage):  # pylint: disable=R0903
    """
    Strategy for managing Milvus dB collections.
    """

    _collections = {}  # Cache to store collections based on path and collection name

    class Config(BaseDataStorage.Config):
        """
        Configuration for MilvusCollectionDataStorage.
        """
        path: str = Field(
            ...,
            description="Path to the database."
        )
        vector_dimension: Optional[int] = Field(
            768,
            description="Dimension of the vector embeddings."
        )
        metric_type: Optional[str] = Field(
            "COSINE",
            description="Vector dB metric."
        )
        text_max_lenght: Optional[int] = Field(
            512,
            description="Max length of the text description."
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MilvusCollectionDataStorage with the given configuration.

        :param config: Dictionary containing configuration values.
        """
        self.config = MilvusCollectionDataStorage.Config(**config)
        self.result = MilvusCollectionDataStorage.Result()
        collection_key = (self.config.path, self.config.collection)
        if collection_key not in MilvusCollectionDataStorage._collections or self.config.reset:
            collection = self._create_or_retrieve_collection()
            MilvusCollectionDataStorage._collections[collection_key] = collection
        self._milvus_collection = MilvusCollectionDataStorage._collections[collection_key]

    def _create_or_retrieve_collection(self):
        """
        Create or retrieve a MilvusCollectionDataStorage dB collection.

        :return: The MilvusCollectionDataStorage dB collection name.
        """
        milvus_client = MilvusClient(self.config.path)
        logger.debug(
            f"Attempting to get or create Milvus dB collection '{self.config.collection}'.")
        collection_list = milvus_client.list_collections()
        collection_name = self.config.collection
        if collection_name not in collection_list:
            self._create_collection(milvus_client)
        elif self.config.reset:
            milvus_client.drop_collection(collection_name=collection_name)
            self._create_collection(milvus_client)
        collection = {
            "client": milvus_client,
            "name": collection_name,
        }
        return collection

    def _create_collection(self, client):
        """
        Create or retrieve a MilvusCollectionDataStorage dB collection.

        : param: Milvus client
        """
        schema = self._create_collection_schema()
        index_params = self._create_indexes(client)
        client.create_collection(
            collection_name=self.config.collection,
            schema=schema,
            index_params=index_params,
        )

    def _create_collection_schema(self):
        """
        Create or retrieve a Collechion Chema collection.

        :return: The collection schema.
        """
        id_field = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            description="int64",
            is_primary=True,
            auto_id=True,
        )
        embedding_field = FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            description="float vector",
            dim=self.config.vector_dimension,
            is_primary=False
        )
        text_field = FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            description="text of the chunk",
            max_length=self.config.text_max_lenght,
            is_primary=False
        )
        fields=[id_field, embedding_field, text_field]
        return CollectionSchema(
            fields=fields,
            description="Vector dB used in the platform",
            enable_dynamic_field=True)

    def _create_indexes(self, client):
        """
        Create the collection indexes.

        : param: Milvus client
        :return: The collection indexes.
        """
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type=self.config.metric_type
        )
        return index_params

    def get_collection(self) -> 'MilvusCollectionDataStorage.Result':
        """
        Retrieve the Milvus dB collection based on the current configuration.

        :return: Result object containing the collection or error details.
        """
        try:
            self.result.status = "success"
            self.result.collection = self._milvus_collection
            logger.debug("Successfully retrieved the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while retrieving the collection: {e}"
            logger.error(self.result.error_message)
        return self.result
