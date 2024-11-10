#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Data Retriever

Placeholder class that has to be overwritten
"""

import abc
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BaseDataRetriever(abc.ABC):  # pylint: disable=R0903
    """
    Base Data Retriever
    """

    class Config(BaseModel):
        """
        Arguments of the Data Loader class
        """
        type: str = Field(
            ...,
            description="Type of the retriever"
        )
        include: Optional[List[str]] = Field(
            ["documents", "metadatas"],
            description="Fields to include in the retrieval results."
        )
        n_results: Optional[int] = Field(
            10,
            description="Number of chunks to use for retrieval."
        )

    class Result(BaseModel):
        """
        Result of the data storage operation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        elements: Optional[List[Dict[str, Any]]] = Field(
            None,
            description="Retrieved document elements and their data and metadata."
        )

    @abc.abstractmethod
    def select(self, collection, query):
        """
        Retrieve data from the Chroma dB collection based on the provided query.

        :param collection: Chroma collection to query.
        :param query: Query string to search for in the collection.
        :return: Result object indicating the success or failure of the operation.
        """
