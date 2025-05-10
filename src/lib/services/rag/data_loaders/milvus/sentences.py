#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Milvus for Sentences Data Loader

This module provides functionality to:
- Retrieve or create a Milvus collection by name
- Load data and metadata into the collection using embeddings from the metadata
"""

from typing import Dict, List, Any, Tuple
from tqdm import tqdm
from src.lib.services.rag.data_loaders.base import BaseDataLoader
from src.lib.core.log import Logger

logger = Logger().get_logger()


class MilvusForSentenceDataLoader(BaseDataLoader):  # pylint: disable=R0903
    """
    Data loader strategy for managing Milvus collections with sentence embeddings.
    Embeddings should be present in the metadata of each element.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data loader with the given configuration.

        :param config: Configuration dictionary for the data loader.
        """
        self.config = MilvusForSentenceDataLoader.Config(**config)
        self.result = MilvusForSentenceDataLoader.Result()

    def insert(
            self,
            collection: Dict,
            elements: List[Dict[str, Any]]
        ) -> 'MilvusForSentenceDataLoader.Result':
        """
        Insert data into the Milvus collection.

        :param collection: Milvus collection dict with client and name.
        :param elements: List of dictionaries containing 'text',
            'metadata', and 'embedding' for insertion.
        :return: Result object indicating the success or failure of the operation.
        """
        try:
            self.result.status = "success"
            documents, metadatas, embeddings = self._convert_to_documents(elements)
            self._insert_documents_into_collection(collection, embeddings, documents, metadatas)
            logger.debug("Successfully inserted elements into the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while inserting data: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _convert_to_documents(
            self,
            elements: List[Dict[str, Any]]
        ) -> Tuple[List[str], List[Dict[str, Any]], List[List[float]]]:
        """
        Validate and split the input elements into documents, metadata, and embeddings.

        :param elements: List of dictionaries containing 'text', 'metadata', and 'embedding'.
        :return: Tuple containing a list of documents,
            a list of their corresponding metadata, and embeddings.
        :raises ValueError: If an embedding is missing or invalid.
        """
        documents = []
        metadatas = []
        embeddings = []
        for element in tqdm(elements, desc="Validating and processing elements"):
            # Extract text
            text = element.get('text', '')
            documents.append(text)
            # Extract metadata and remove embedding from it before validation
            metadata = element.get('metadata', {})
            # Extract embedding first
            embedding = metadata.pop('embedding', None)  # Remove 'embedding' from metadata
            # Validate embedding
            if embedding is None:
                raise ValueError(f"Invalid or missing embedding for element: {text}")
            embeddings.append(embedding)
            # Validate remaining metadata (excluding embedding)
            validated_metadata = {
                key: (value if isinstance(value, (str, int, float, bool)) else str(value))
                for key, value in metadata.items()
            }
            metadatas.append(validated_metadata)
        return documents, metadatas, embeddings

    def _insert_documents_into_collection(
            self,
            collection: Dict,
            embeddings: List[List[float]],
            documents: List[str],
            metadatas: List[Dict[str, Any]]):
        """
        Insert documents, their embeddings, and corresponding metadata into the Milvus collection.

        :param collection: Milvus collection dict with client and name.
        :param embeddings: List of vector embeddings corresponding to the documents.
        :param documents: List of document texts to insert.
        :param metadatas: List of metadata dictionaries corresponding to the documents.
        """
        client = collection["client"]
        collection_name = collection["name"]
        data = [
            {
                "embedding": embedding,
                "text": document,
                **metadata
            }
            for document, embedding, metadata in zip(documents, embeddings, metadatas)
        ]
        result = client.insert(
            collection_name=collection_name,
            data=data
        )
        logger.debug(f"Inserted {len(documents)} documents into the collection.")
        logger.debug(result)
