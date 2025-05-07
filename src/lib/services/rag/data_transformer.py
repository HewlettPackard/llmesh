#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataTransformer Module

This module defines the DataTransformer class and associated class for 
parsing documents.
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.rag.data_transformers.cte_action_runner import (
    CteActionRunnerDataTransformer
)


class DataTransformer:  # pylint: disable=R0903
    """
    Return the appropriate Data Transformer based on the provided configuration.

    :param config: Configuration dictionary containing the type of trasnformer.
    :return: An instance of the selected data transformer.
    :raises ValueError: If 'type' is not in config or an unsupported type is provided.
    """

    _transformers: Dict[str, Type] = {
        'CteActionRunner': CteActionRunnerDataTransformer,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return Data Transformer
        
        :param config: Configuration dictionary containing the type of tranformer actions.
        :return: An instance of the selected data transformer.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        transformer_type = config.get('type')
        if not transformer_type:
            raise ValueError("Configuration must include 'type'.")
        transformer_class = DataTransformer._transformers.get(transformer_type)
        if not transformer_class:
            raise ValueError(f"Unsupported extractor type: {transformer_type}")
        return transformer_class(config)
