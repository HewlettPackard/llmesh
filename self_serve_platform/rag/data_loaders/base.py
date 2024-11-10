#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Data Loader

Placeholder class that has to be overwritten
"""

import abc
from typing import Optional
from pydantic import BaseModel, Field


class BaseDataLoader(abc.ABC):  # pylint: disable=R0903
    """
    Base Data Loader
    """

    class Config(BaseModel):
        """
        Arguments of the Data Loader class
        """
        type: str = Field(
            ...,
            description="Type of the loader"
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

    @abc.abstractmethod
    def insert(self, collection, elements):
        """
        Insert data into the Chroma dB collection.

        :param collection: Chroma dB collection.
        :param elements: List of dictionaries containing 'text' and 'metadata' for insertion.
        :return: Result object indicating the success or failure of the operation.
        """
