#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Qdrant for Sentences Data Retriever

This module provides functionality to:
- Retrieve data and metadata, expanding them by sentence or section
"""

from typing import Optional, List, Dict, Any
from qdrant_client.http.models import Filter, ScoredPoint
from pydantic import Field
from src.lib.services.rag.data_retrievers.base import BaseDataRetriever
from src.lib.core.log import Logger


logger = Logger().get_logger()


class QdrantForSentenceDataRetriever(BaseDataRetriever):  # pylint: disable=R0903
    """
    Data retriever strategy for managing Qdrant collections with sentence embeddings.
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
            "Section",
            description="Type of expansion to use for retrieving data "
                        "(e.g., 'Section' or 'Sentence')."
        )
        sentence_window: Optional[int] = Field(
            3,
            description="Number of sentences to consider in the sliding window."
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
        self.config = QdrantForSentenceDataRetriever.Config(**config)
        self.result = QdrantForSentenceDataRetriever.Result()

    def select(self, collection: Dict, query: str) -> 'QdrantForSentenceDataRetriever.Result':
        """
        Retrieve data from the Qdrant collection based on the provided query.

        :param collection: Qdrant collection to query.
        :param query: Query string to search for in the collection.
        :return: Result object indicating the success or failure of the operation.
        """
        try:
            self.result.status = "success"
            initial_results = self._retrieve_chunks(collection, query)
            expanded_results = self._expand_results(collection, initial_results)
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
        # Perform a vector search using Qdrant based on the query's embedding
        query_embedding = self.config.embedding_function.embed(query)  # pylint: disable=E1101
        results = collection["client"].search(
            collection_name=collection["name"],
            query_vector=query_embedding,
            limit=self.config.n_results,
            with_payload=True
        )
        return results

    def _expand_results(self, collection_name: str, results: List[ScoredPoint]):
        if self.config.expansion_type == "Section":
            logger.debug("Expanding results by section.")
            expanded_results = self._expand_with_section_window(
                collection_name, results
            )
        elif self.config.expansion_type == "Sentence":
            logger.debug("Expanding results by sentence window.")
            expanded_results = self._expand_with_sentence_window(
                collection_name, results
            )
        else:
            logger.debug("Returning raw results without expansion.")
            expanded_results = results
        return expanded_results

    def _expand_with_section_window(self, collection: Any, results: List[ScoredPoint]):
        expanded_results = results
        processed_headers = set()  # Track processed headers
        for result in results:
            metadata = result.payload
            if metadata["header"] in processed_headers:
                continue
            section_results = collection["client"].scroll(
                collection_name=collection["name"],
                filter=Filter(must=[{"key": "header", "match": {"value": metadata["header"]}}]),
                with_payload=True
            )
            merged_docs = self._order_and_merge(
                [sr.id for sr in section_results],
                [sr.payload['documents'] for sr in section_results])
            result.payload['documents'] = merged_docs
            processed_headers.add(metadata["header"])
        return expanded_results

    def _order_and_merge(self, ids: List[str], documents: List[str]) -> str:
        paired = sorted(zip(map(int, ids), documents))
        sorted_documents = [doc for _, doc in paired]
        return " ".join(sorted_documents)

    def _expand_with_sentence_window(self, collection: Any, results: List[ScoredPoint]):
        expanded_results = results
        total_count = collection["client"].count(collection_name=collection["name"]).count
        for result in results:
            index = int(result.id)
            ids = self._create_id_vector(index, self.config.sentence_window, total_count)
            sentence_results = collection["client"].scroll(
                collection_name=collection["name"],
                ids=ids,
                with_payload=True
            )
            merged_docs = self._order_and_merge(
                [sr.id for sr in sentence_results],
                [sr.payload['documents'] for sr in sentence_results])
            result.payload['documents'] = merged_docs
        return expanded_results

    def _create_id_vector(self, index: int, window: int, max_value: int) -> List[str]:
        start = max(0, index - window)
        end = min(max_value, index + window)
        return [str(i) for i in range(start, end) if i != index]

    def _process_results(self, results: List[ScoredPoint]):
        documents = [r.payload['text'] for r in results]
        metadatas = [{k: v for k, v in r.payload.items() if k != 'text'} for r in results]
        embeddings = [r.vector for r in results]
        distances = [r.score for r in results]
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
