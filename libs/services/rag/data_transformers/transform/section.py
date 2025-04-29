#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides functions to transform elements' text into sections
using different methods.
"""

import re
from typing import List, Dict, Any


def transform_section_by_header(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform sections by header.

    :param elements: List of elements with text data
    :return: List of elements transformed into sections by header
    """
    return _merge_elements_below_header(elements)

def transform_section_by_type(
        header_types: List[str],
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Transform sections by element type.

    :param header_types: List of header types to consider for sectioning
    :param elements: List of elements with text data
    :return: List of elements transformed into sections by type
    """
    for element in elements:
        if element["metadata"]["type"] in header_types:
            element["metadata"]["header"] = element["text"]
        else:
            element["metadata"]["header"] = None
    return _merge_elements_below_header(elements)

def transform_section_by_toc(
        toc_types: List[str],
        toc_pattern: str, elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Transform sections based on table of contents (TOC).

    :param toc_types: List of element types to consider for TOC extraction
    :param toc_pattern: Regular expression pattern to identify TOC entries
    :param elements: List of elements with text data
    :return: List of elements transformed into sections based on TOC
    """
    toc_elements = []
    new_elements = []
    title_pattern = r'(.+)$'
    for element in elements:
        if element["metadata"]["type"] in toc_types:
            match = re.search(toc_pattern, element["text"])
            if match:
                toc_header = _clean_text(match.group(1))
                toc_elements.append(toc_header)
        else:
            new_elements.append(element)
            # Assuming that TOC is at the beginning of the document
            element_text_cleaned = _clean_text(element["text"])
            for toc in toc_elements:
                match = re.search(title_pattern, element_text_cleaned)
                if match and match.group(1) == toc:
                    element["metadata"]["header"] = element_text_cleaned
    return _merge_elements_below_header(new_elements)

def _merge_elements_below_header(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge elements below their respective headers.

    :param elements: List of elements with text data
    :return: List of merged elements below headers
    """
    new_elements = []
    previous_element = None
    for element in elements:
        if element["metadata"]["header"]:
            if previous_element:
                new_elements.append(previous_element)
            previous_element = element
        else:
            if previous_element:
                previous_element["text"] += '\n' + element["text"]  # pylint: disable=E1137
            else:
                previous_element = element
    if previous_element:
        new_elements.append(previous_element)
    return new_elements

def _clean_text(text: str) -> str:
    """
    Clean text by replacing tabs with spaces and removing extra spaces.

    :param text: Text to be cleaned
    :return: Cleaned text
    """
    return ' '.join(text.replace('\t', ' ').split())
