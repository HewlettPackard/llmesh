#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the functionality of the text cleaning functions.
It includes tests for removing multiple spaces, replacing tabs with spaces,
removing title elements only, removing sections by header, keeping sections by header,
and removing short sections.
"""

import os
import pytest
from self_serve_platform.rag.data_transformers.clean_regex import (
    remove_multiple_spaces,
    replace_tabs_with_spaces,
    remove_title_elements_only,
    remove_sections_by_header,
    keep_sections_by_header,
    remove_short_sections,
)


@pytest.fixture
def sample_elements():
    """
    Fixture to create a sample list of elements with text and metadata.

    Returns:
        List[Dict[str, Any]]: A list of sample elements.
    """
    return [
        {
            "text": "This is   a  sample text.  ",
            "metadata": {
                "header": "Sample Header"
            }
        },
        {
            "text": "Another\t\tsample\ttext.",
            "metadata": {
                "header": "Another Header"
            }
        },
        {
            "text": "Short",
            "metadata": {
                "header": "Short Header"
            }
        }
    ]

def test_remove_multiple_spaces(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that multiple spaces in text fields are removed.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    cleaned_elements = remove_multiple_spaces(sample_elements)
    assert cleaned_elements[0]['text'] == "This is a sample text."
    assert cleaned_elements[1]['text'] == "Another sample text."


def test_replace_tabs_with_spaces(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that tabs in text fields are replaced with spaces.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    clean_fields = ["text"]
    cleaned_elements = replace_tabs_with_spaces(clean_fields, sample_elements)
    assert cleaned_elements[1]['text'] == "Another  sample text."


def test_remove_title_elements_only(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that elements with text matching the header metadata are removed.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    sample_elements[0]['text'] = "Sample Header"
    cleaned_elements = remove_title_elements_only(sample_elements)
    assert len(cleaned_elements) == 2
    assert cleaned_elements[0]['text'] == "Another\t\tsample\ttext."


def test_remove_sections_by_header(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that elements with specified headers are removed.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    headers_to_remove = ["Sample Header"]
    cleaned_elements = remove_sections_by_header(headers_to_remove, sample_elements)
    assert len(cleaned_elements) == 2
    assert cleaned_elements[0]['metadata']['header'] == "Another Header"


def test_keep_sections_by_header(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that only elements with specified headers are kept.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    headers_to_keep = ["Another Header"]
    cleaned_elements = keep_sections_by_header(headers_to_keep, sample_elements)
    assert len(cleaned_elements) == 1
    assert cleaned_elements[0]['metadata']['header'] == "Another Header"


def test_remove_short_sections(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that elements with text shorter than the minimum length are removed.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    min_section_length = 10
    cleaned_elements = remove_short_sections(min_section_length, sample_elements)
    assert len(cleaned_elements) == 2
    assert cleaned_elements[0]['text'] == "This is   a  sample text.  "


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
