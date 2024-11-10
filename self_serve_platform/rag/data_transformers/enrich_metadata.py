#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides methods for enriching metadata of text elements using configuration settings.
"""

from typing import List, Dict, Any


def add_metadata(metadata, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich metadata of elements based on the configuration provided.

    If the configuration specifies enrichment for metadata, this function will add or update
    metadata fields for each element. The values for these metadata fields can be either
    fixed values or callable functions. If the value is a callable, it will be called with 
    the element as its argument, and the result will be used as the metadata value.

    :param metadata: List of metadata to add
    :param elements: List of elements to enrich with additional metadata
    :return: List of elements with enriched metadata
    """
    if metadata is not None:
        for element in elements:
            for key, value in metadata.items():  # pylint: disable=E1101
                if callable(value):
                    element['metadata'][key] = value(element)
                else:
                    element['metadata'][key] = value
    return elements
