#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chroma for Sentences Data Loader

This module provides functionality to:
- Retrieve or create a Chroma collection by name
- Load data and metadata into the collection using internal Chroma Sentence Embedding
"""

from typing import Dict, List, Any, Tuple
from tqdm import tqdm
from src.lib.services.rag.data_loaders.base import BaseDataLoader
from src.lib.core.log import Logger


logger = Logger().get_logger()


class ChromaForSentenceDataLoader(BaseDataLoader):  # pylint: disable=R0903
    """
    Data loader strategy for managing Chroma dB collections with sentence embeddings.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data loader with the given configuration.

        :param config: Configuration dictionary for the data loader.
        """
        self.config = ChromaForSentenceDataLoader.Config(**config)
        self.result = ChromaForSentenceDataLoader.Result()

    def insert(
            self,
            collection: Any,
            elements: List[Dict[str, Any]]
        ) -> 'ChromaForSentenceDataLoader.Result':
        """
        Insert data into the Chroma dB collection.

        :param collection: Chroma dB collection.
        :param elements: List of dictionaries containing 'text' and 'metadata' for insertion.
        :return: Result object indicating the success or failure of the operation.
        """
        try:
            self.result.status = "success"
            documents, metadatas = self._convert_to_documents(elements)
            self._insert_documents_into_collection(collection, documents, metadatas)
            logger.debug("Successfully inserted elements into the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while inserting data: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _convert_to_documents(
            self,
            elements: List[Dict[str, Any]]
        ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Validate and split the input elements into documents and metadata.

        :param elements: List of dictionaries containing 'text' and 'metadata'.
        :return: Tuple containing a list of documents and a list of their corresponding metadata.
        """
        documents = []
        metadatas = []
        for element in tqdm(elements, desc="Validating and processing elements"):
            # Extract text and validate metadata
            text = element.get('text', '')
            documents.append(text)
            metadata = element.get('metadata', {})
            validated_metadata = {
                key: (value if isinstance(value, (str, int, float, bool)) else str(value))
                for key, value in metadata.items()
            }
            metadatas.append(validated_metadata)
        return documents, metadatas

    def _insert_documents_into_collection(
            self,
            chroma_collection: Any,
            documents: List[str],
            metadatas: List[Dict[str, Any]]):
        """
        Insert documents and their corresponding metadata into the Chroma collection.

        :param chroma_collection: Chroma dB collection.
        :param documents: List of document texts to insert.
        :param metadatas: List of metadata dictionaries corresponding to the documents.
        """
        current_count = chroma_collection.count()  # pylint: disable=E1101
        ids = [str(i + current_count) for i in range(len(documents))]
        chroma_collection.add(  # pylint: disable=E1101
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.debug(f"Inserted {len(documents)} documents into the collection.")
