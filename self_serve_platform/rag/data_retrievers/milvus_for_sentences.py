#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Milvus for Sentences Data Retriever

This module provides functionality to:
- Retrieve data and metadata, expanding them by sentence or section
"""

from typing import Optional, List, Dict, Any
from collections import defaultdict
from pydantic import Field
from self_serve_platform.rag.data_retrievers.base import BaseDataRetriever
from self_serve_platform.system.log import Logger


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
        expansion_type: Optional[str] = Field(
            "Group",
            description="Type of expansion to use for retrieving data "
        )
        group_size: Optional[int] = Field(
            5,
            description="Number of chunk to consider in the group."
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
            initial_results = self._retrieve_chunks(collection, query)
            expanded_results = self._expand_results(initial_results)
            self._process_results(expanded_results)
            logger.debug("Successfully retrieved elements from the collection.")
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = (
                f"An error occurred while retrieving data: {e}"
            )
            logger.error(self.result.error_message)
        return self.result

    def _retrieve_chunks(self, collection: Dict, query: str):
        # Perform a vector search using Milvus based on the query's embedding
        query_embedding = self.config.embedding_function.encode_documents(query)  # pylint: disable=E1101
        # Prepare the common arguments for the search
        search_kwargs = {
            "collection_name": collection["name"],
            "anns_field": "embedding",
            "data": [query_embedding],
            "limit": self.config.n_results
        }
        # Conditionally add group-related arguments
        if self.config.expansion_type == "Group":
            search_kwargs["group_by_field"] = "header"
            search_kwargs["group_size"] = self.config.group_size
            search_kwargs["strict_group_size"] = True
        # Perform the search, unpacking the keyword arguments
        results = collection["client"].search(**search_kwargs)
        return results

    def _expand_results(self, results: Any):
        if self.config.expansion_type == "Group":
            logger.debug("Expanding results by header group.")
            expanded_results = self._expand_with_group(results)
        else:
            logger.debug("Returning raw results without expansion.")
            expanded_results = results[0]
        return expanded_results

    def _expand_with_group(self, results: Any):
        # 1. Group items by the 'header' from their entity
        grouped = defaultdict(list)
        for record in results[0]:
            header = record["entity"].get("header", "")
            grouped[header].append(record)
        merged_results = []
        # 2. For each header group:
        #    - gather all text
        #    - find the item with the lowest distance
        #    - use that item's metadata as the "base"
        #    - replace the text field with merged text
        for header, items in grouped.items():
            # Gather all text for this header
            texts = []
            for item in items:
                text = item["entity"].get("text", "")
                texts.append(text)
            # Merge the text any way you prefer (e.g., join with space or newline)
            merged_text = "\n".join(texts)
            # Find the item with the lowest distance in this group
            lowest_distance_item = min(items, key=lambda x: x["distance"])
            # Build the new merged item using the metadata from the lowest-distance item
            # and the merged text
            merged_item = {
                "id": lowest_distance_item["id"],
                "distance": lowest_distance_item["distance"],
                "entity": {
                    **lowest_distance_item["entity"],
                    "text": merged_text,
                }
            }
            merged_results.append(merged_item)
        return merged_results

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
