#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chroma for Sentences Data Retriever

This module provides functionality to:
- Retrieve data and metadata, expanding them by sentence or section
- Plot data in a 2D space using UMAP for dimensionality reduction
"""

from typing import Optional, List
import umap.umap_ as umap
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from pydantic import Field
from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import (
    SentenceTransformerEmbeddingFunction)
from src.lib.services.rag.data_retrievers.base import BaseDataRetriever
from src.lib.core.log import Logger


logger = Logger().get_logger()


class ChromaForSentenceDataRetriever(BaseDataRetriever):  # pylint: disable=R0903
    """
    Data retriever strategy for managing Chroma dB collections with sentence embeddings.
    """

    class Config(BaseDataRetriever.Config):
        """
        Configuration for ChromaForSentenceDataRetriever.
        """
        expansion_type: Optional[str] = Field(
            "Section",
            description="Type of expansion to use for retrieving data "
                        "(e.g., 'Section' or 'Sentence')."
        )
        sentence_window: Optional[int] = Field(
            3,
            description="Number of sentences to consider in the sliding window."
        )
        max_plot: Optional[int] = Field(
            1000,
            description="Maximum number of points to plot."
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
        self.config = ChromaForSentenceDataRetriever.Config(**config)
        self.result = ChromaForSentenceDataRetriever.Result()

    def select(self, collection, query: str) -> 'ChromaForSentenceDataRetriever.Result':
        """
        Retrieve data from the Chroma dB collection based on the provided query.

        :param collection: Chroma collection to query.
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

    def _retrieve_chunks(self, chroma_collection, query: str):
        results = chroma_collection.query(
            query_texts=[query],
            n_results=self.config.n_results,
            include=self.config.include
        )
        return results

    def _expand_results(self, chroma_collection, results):
        if self.config.expansion_type == "Section":
            logger.debug("Expanding results by section.")
            expanded_results = self._expand_with_section_window(
                chroma_collection, results
            )
        elif self.config.expansion_type == "Sentence":
            logger.debug("Expanding results by sentence window.")
            expanded_results = self._expand_with_sentence_window(
                chroma_collection, results
            )
        else:
            logger.debug("Returning raw results without expansion.")
            expanded_results = results
        return expanded_results

    def _expand_with_section_window(self, chroma_collection, results):
        expanded_results = results
        processed_headers = set()  # Track processed headers
        for i, metadata in enumerate(results['metadatas'][0]):
            if metadata["header"] in processed_headers:
                expanded_results['documents'][0][i] = ""
                continue
            section_results = chroma_collection.get(
                where={"header": metadata["header"]},
                include=['documents']
            )
            expanded_results['documents'][0][i] = self._order_and_merge(
                section_results['ids'], section_results['documents']
            )
            processed_headers.add(metadata["header"])
        return expanded_results

    def _order_and_merge(self, ids: List[str], documents: List[str]) -> str:
        paired = sorted(zip(map(int, ids), documents))
        sorted_documents = [doc for _, doc in paired]
        return " ".join(sorted_documents)

    def _expand_with_sentence_window(self, chroma_collection, results):
        expanded_results = results
        total_count = chroma_collection.count()
        for i, index in enumerate(results['ids'][0]):
            ids = self._create_id_vector(
                int(index), self.config.sentence_window, total_count
            )
            sentence_results = chroma_collection.get(
                ids=ids, include=['documents']
            )
            expanded_results['documents'][0][i] = self._order_and_merge(
                sentence_results['ids'], sentence_results['documents']
            )
        return expanded_results

    def _create_id_vector(self, index: int, window: int, max_value: int) -> List[str]:
        start = max(0, index - window)
        end = min(max_value, index + window)
        return [str(i) for i in range(start, end) if i != index]

    def _process_results(self, results):
        documents = self._get_results_field(results, "documents")
        metadatas = self._get_results_field(results, "metadatas")
        embeddings = self._get_results_field(results, "embeddings")
        distances = self._get_results_field(results, "distances")
        if documents and metadatas:
            combined_result = self._combine_elements(
                documents, metadatas, embeddings, distances
            )
            self.result.elements = combined_result["elements"]
            self.result.embeddings = combined_result["embeddings"]
            self.result.distances = combined_result["distances"]
        else:
            self.result.elements = None
            self.result.embeddings = None
            self.result.distances = None

    def _get_results_field(self, results, field: str):
        field_elements = results.get(field)
        return field_elements[0] if field_elements else None

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


    def plot(self, collection, query: str):
        """
        Plot data from Chroma dB in 2D space using UMAP.
        """
        logger.debug("Plotting embeddings in 2D space.")
        max_embeddings = self.config.max_plot
        embeddings = collection.get(
            include=['embeddings']
        )['embeddings'][:max_embeddings]
        umap_transform = umap.UMAP(
            random_state=0, transform_seed=0
        ).fit(embeddings)
        projected_embeddings = {
            "dataset": self._project_embeddings(embeddings, umap_transform),
            "query": self._project_embeddings(
                [SentenceTransformerEmbeddingFunction()([query])[0]],
                umap_transform
            ),
            "chunks": self._project_embeddings(
                self.select(collection, query).embeddings, umap_transform
            )
        }
        self._plot_projected_embeddings(projected_embeddings)

    def _project_embeddings(self, embeddings: List[np.ndarray], umap_transform) -> np.ndarray:
        return np.array([
            umap_transform.transform([embedding])[0]
            for embedding in tqdm(embeddings)
        ])

    def _plot_projected_embeddings(self, projected_embeddings):
        plt.figure()
        plt.scatter(
            projected_embeddings["dataset"][:, 0],
            projected_embeddings["dataset"][:, 1],
            s=10, color='gray'
        )
        plt.scatter(
            projected_embeddings["query"][:, 0],
            projected_embeddings["query"][:, 1],
            s=150, marker='X', color='r'
        )
        plt.scatter(
            projected_embeddings["chunks"][:, 0],
            projected_embeddings["chunks"][:, 1],
            s=100, facecolors='none', edgecolors='g'
        )
        plt.gca().set_aspect('equal', 'datalim')
        plt.title('IntelliGen RAG Embeddings')
        plt.axis('off')
        plt.show()
