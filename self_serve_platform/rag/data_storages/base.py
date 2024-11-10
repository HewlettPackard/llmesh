#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Data Storage

Abstract base class for data storage implementations.
"""

import abc
from typing import Optional, Any
from pydantic import BaseModel, Field


class BaseDataStorage(abc.ABC):  # pylint: disable=R0903
    """
    Abstract base class for data storage implementations.
    """

    class Config(BaseModel):
        """
        Configuration for the Data Storage class.
        """
        type: str = Field(
            ...,
            description="Type of the data storage."
        )
        collection: str = Field(
            ...,
            description="Name of the collection within the database."
        )
        reset: Optional[bool] = Field(
            False,
            description="Flag to reset the collection."
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
        collection: Optional[Any] = Field(
            None,
            description="Requested collection."
        )

    @abc.abstractmethod
    def get_collection(self) -> Any:
        """
        Retrieve the data collection.

        :return: The requested data collection.
        """
