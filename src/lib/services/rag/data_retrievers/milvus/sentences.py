#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Milvus for Sentences Data Retriever

This module provides functionality to:
- Retrieve data and metadata, expanding them by sentence or section
"""

from typing import Optional, List, Dict, Any
from pydantic import Field
from src.lib.services.rag.data_retrievers.base import BaseDataRetriever
from src.lib.core.log import Logger


logger = Logger().get_logger()


class MilvusForSentenceDataRetriever(BaseDataRetriever):  # pylint: disable=R0903
    """
    Data retriever strategy for managing Milvus collections with sentence embeddings.
    """

    class Config(BaseDataRetriever.Config):
        """
        Configuration for QdrantForSentenceDataRetriever.
        """
        embedding_function: Any = Field(
            ...,
            description="Embedding function to be used for the query"
        )
        output_fields: Optional[List] = Field(
            ['text', 'header'],
            description="Fields to return"
        )

    class Result(BaseDataRetriever.Result):
        """
        Result of the data retrieval process.
        """
        embeddings: Optional[List] = Field(
            None,
            description="List of retrieved embeddings."
        )
        distances: Optional[List] = Field(
            None,
            description="List of distances associated with the retrieved embeddings."
        )

    def __init__(self, config: dict):
        """
        Initialize the data retriever with the given configuration.

        :param config: Dictionary containing configuration parameters.
        """
        self.config = MilvusForSentenceDataRetriever.Config(**config)
        self.result = MilvusForSentenceDataRetriever.Result()

    def select(self, collection: Dict, query: str) -> 'MilvusForSentenceDataRetriever.Result':
        """
        Retrieve data from the Milvus collection based on the provided query.

        :param collection: Milvus collection to query.
        :param query: Query string to search for in the collection.
        :return: Result object indicating the success or failure of the operation.
        """
        try:
            self.result.status = "success"
            query_embedding = self.config.embedding_function.encode_documents([query])  # pylint: disable=E1101
            results = self._retrieve_chunks(collection, query_embedding)
            self._process_results(results[0])
            logger.debug("Successfully retrieved elements from the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = (
                f"An error occurred while retrieving data: {e}"
            )
            logger.error(self.result.error_message)
        return self.result

    def _retrieve_chunks(self, collection: Dict, query_embedding: Any):
        # Prepare the common arguments for the search
        search_kwargs = {
            "collection_name": collection["name"],
            "anns_field": "embedding",
            "data": query_embedding,
            "limit": self.config.n_results
        }
        if self.config.output_fields:
            search_kwargs["output_fields"] = self.config.output_fields
        # Perform the search, unpacking the keyword arguments
        results = collection["client"].search(**search_kwargs)
        logger.debug(f'Retrieved {len(results)}')
        return results

    def _process_results(self, results: Dict):
        documents = [r['entity']['text'] for r in results]
        metadatas = [
            {k: v for k, v in r['entity'].items() if k not in ('text', 'embedding')}
            for r in results
        ]
        embeddings = [r['entity']['embedding'] for r in results]
        distances = [r['distance'] for r in results]
        if documents and metadatas:
            combined_result = self._combine_elements(documents, metadatas, embeddings, distances)
            self.result.elements = combined_result["elements"]
            self.result.embeddings = combined_result["embeddings"]
            self.result.distances = combined_result["distances"]
        else:
            self.result.elements = None
            self.result.embeddings = None
            self.result.distances = None

    def _combine_elements(self, documents, metadatas, embeddings, distances):
        elements = []
        valid_embeddings = [] if embeddings else None
        valid_distances = [] if distances else None
        for i, (text, metadata) in enumerate(zip(documents, metadatas)):
            if text:
                elements.append({"text": text, "metadata": metadata})
                if valid_embeddings is not None:
                    valid_embeddings.append(embeddings[i])
                if valid_distances is not None:
                    valid_distances.append(distances[i])

        return {
            "elements": elements,
            "embeddings": valid_embeddings,
            "distances": valid_distances
        }
