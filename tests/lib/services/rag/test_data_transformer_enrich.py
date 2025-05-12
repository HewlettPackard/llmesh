#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the functionality of the metadata enrichment functions.
It includes tests for adding metadata with fixed values and callable functions.
"""

import os
import pytest
from src.lib.services.rag.data_transformers.enrich.metadata import add_metadata


@pytest.fixture
def sample_elements():
    """
    Fixture to create a sample list of elements with text and metadata.

    Returns:
        List[Dict[str, Any]]: A list of sample elements.
    """
    return [
        {
            "text": "Sample text 1",
            "metadata": {
                "header": "Header 1"
            }
        },
        {
            "text": "Sample text 2",
            "metadata": {
                "header": "Header 2"
            }
        }
    ]


def test_add_fixed_metadata(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that fixed metadata is added to each element.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    metadata = {
        "author": "John Doe",
        "length": 100
    }
    enriched_elements = add_metadata(metadata, sample_elements)
    assert all(element['metadata']['author'] == "John Doe" for element in enriched_elements)
    assert all(element['metadata']['length'] == 100 for element in enriched_elements)


def test_add_callable_metadata(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that callable metadata is added to each element by invoking the callable.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    metadata = {
        "author": lambda element: "Author " + element['metadata']['header'].split()[-1],
        "length": lambda element: len(element['text'])
    }
    enriched_elements = add_metadata(metadata, sample_elements)
    assert enriched_elements[0]['metadata']['author'] == "Author 1"
    assert enriched_elements[1]['metadata']['author'] == "Author 2"
    assert enriched_elements[0]['metadata']['length'] == len(sample_elements[0]['text'])
    assert enriched_elements[1]['metadata']['length'] == len(sample_elements[1]['text'])


def test_add_mixed_metadata(sample_elements):  # pylint: disable=W0621
    """
    Test to verify that a mix of fixed and callable metadata is added to each element.

    Args:
        sample_elements (List[Dict[str, Any]]): A fixture providing sample elements.
    """
    metadata = {
        "author": "Jane Doe",
        "length": lambda element: len(element['text'])
    }
    enriched_elements = add_metadata(metadata, sample_elements)
    assert all(element['metadata']['author'] == "Jane Doe" for element in enriched_elements)
    assert enriched_elements[0]['metadata']['length'] == len(sample_elements[0]['text'])
    assert enriched_elements[1]['metadata']['length'] == len(sample_elements[1]['text'])


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
