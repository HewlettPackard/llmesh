#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides methods for cleaning text data using several techniques.
"""

from typing import Optional, List, Dict, Any


def remove_multiple_spaces(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove multiple spaces from text fields specified in the config.
    
    :param elements: List of elements with text data
    :return: List of elements with multiple spaces removed from text fields
    """
    for element in elements:
        element['text'] = ' '.join(element['text'].split())
    return elements

def replace_tabs_with_spaces(clean_fields, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Replace tabs with spaces in text fields specified in the config.
    
    :param clean_fields: List of field types to clean
    :param elements: List of elements with text data
    :return: List of elements with tabs replaced by spaces in text fields
    """
    for element in elements:
        for key in clean_fields:
            if key in element:
                element[key] = _replace_tabs_in_text(element[key])
            elif key in element['metadata']:
                element['metadata'][key] = _replace_tabs_in_text(element['metadata'][key])
    return elements

def _replace_tabs_in_text(text: Optional[str]) -> Optional[str]:
    """
    Replace tabs with spaces in a given text.
    
    :param text: Text to process
    :return: Text with tabs replaced by spaces
    """
    return text.replace('\t', ' ') if text else text

def remove_title_elements_only(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove elements where the text matches the header metadata.
    
    :param config: Configuration object containing clean_fields attribute
    :param elements: List of elements with text data
    :return: List of elements with matching text and header removed
    """
    return [
        element for element in elements
        if element['text'] != element['metadata'].get('header')
    ]

def remove_sections_by_header(
        headers_to_remove,
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Remove elements based on headers specified in the config.
    
    :param headers_to_remove: List of headers to remove
    :param elements: List of elements with text data
    :return: List of elements with specified headers removed
    """
    return [
        element for element in elements
        if element['metadata'].get('header') not in headers_to_remove
    ]

def keep_sections_by_header(
        headers_to_keep,
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Keep only elements with headers specified in the config.
    
    :param headers_to_remove: List of headers to kepp
    :param elements: List of elements with text data
    :return: List of elements with only specified headers
    """
    return [
        element for element in elements
        if element['metadata'].get('header') in headers_to_keep
    ]

def remove_short_sections(
        min_section_length,
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Remove elements with text shorter than the minimum length specified in the config.
    
    :param min_section_length: Minimum length of a section
    :param elements: List of elements with text data
    :return: List of elements with text longer than the minimum length
    """
    return [
        element for element in elements
        if len(element.get("text", "")) >= min_section_length
    ]
