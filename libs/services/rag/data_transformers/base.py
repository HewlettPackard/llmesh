#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Data Transformer

Placeholder class that has to be overwritten
"""

import abc
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field


class BaseDataTransformer(abc.ABC):  # pylint: disable=R0903
    """
    Base Data Transformer
    """

    class Config(BaseModel):
        """
        Configuration for the Data Transformer class.
        """
        type: str = Field(
            ...,
            description="Type of the transformer deployment."
        )
        clean: Optional["BaseDataTransformer.ConfigClean"] = Field(
            None,
            description="Configuration fields of the clean operation"
        )
        transform: Optional["BaseDataTransformer.ConfigTransform"] = Field(
            None,
            description="Configuration fields of the transform operation"
        )
        enrich: Optional["BaseDataTransformer.ConfigEnrich"] = Field(
            None,
            description="Configuration fields of the enrich operation"
        )

    class ConfigClean(BaseModel):
        """
        Configuration for the Data Transformer clean sub-class.
        """
        fields: Optional[List[str]] = Field(
            ['header', 'text'],
            description="List of element fields to clean, used in tab cleaning"
        )

    class ConfigTransform(BaseModel):
        """
        Configuration for the Data Transformer clean sub-class.
        """

    class ConfigEnrich(BaseModel):
        """
        Configuration for the Data Transformer clean sub-class.
        """
        metadata: Optional[Dict[str, Any]] = Field(
            None,
            description="List of metadata to add"
        )

    class Result(BaseModel):
        """
        Result of the data transformation process.
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
            description="Trasnformed document elements and their data and metadata."
        )

    @abc.abstractmethod
    def process(
            self,
            actions: List[str],
            elements: List[Dict[str, Any]]
        ) -> 'BaseDataTransformer.Result':
        """
        Perform the specified CTE actions on the provided elements.
        
        :param actiosn: List of actions to perform
        :param elements: Elements to transform
        :return: Result object containing the trasnformed elements
        """
