#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataRetriever factory and the MilvusForSentenceDataRetriever class.
It ensures that the factory method correctly initializes and returns instances of the 
appropriate retriever types based on the given configuration. It also tests the behavior of 
the retriever's select method to ensure correct data retrieval and processing.
"""

import os
from unittest.mock import patch, MagicMock
import pytest

# Adjust these imports to match your actual code structure:
from src.lib.services.rag.data_retriever import DataRetriever
from src.lib.services.rag.data_retrievers.milvus.sentences import (
    MilvusForSentenceDataRetriever
)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "MilvusForSentences",
            "embedding_function": MagicMock(),  # mock embedding_function
            "n_results": 3
        },
        MilvusForSentenceDataRetriever
    )
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct class
    based on the configuration provided.
    """
    retriever_instance = DataRetriever.create(config)
    assert isinstance(retriever_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError, match="Unsupported extractor type: InvalidType"):
        DataRetriever.create({"type": "InvalidType"})


@pytest.fixture
def milvus_retriever_config():
    """
    Fixture to provide a mock configuration for MilvusForSentenceDataRetriever.
    """
    return {
        "type": "MilvusForSentences",
        "embedding_function": MagicMock(),
        "n_results": 3,
    }


@patch('src.lib.services.rag.data_retrievers.milvus.sentences.Logger.get_logger')
@patch('pymilvus.MilvusClient')
def test_select_success(mock_milvus_client, mock_get_logger, milvus_retriever_config):  # pylint: disable=W0621
    """
    Test the select method to ensure it successfully retrieves
    data from Milvus and processes it correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Mock Milvus collection behavior
    mock_collection = {
        "client": mock_milvus_client,
        "name": "test_milvus_collection"
    }
    # Simulate search result from Milvus
    # The search result is typically a list of lists:
    #   The outer list is for each query in "data"
    #   The inner list is the actual search hits
    mock_search_result = [[
        {
            "id": 10,
            "distance": 0.123,
            "entity": {
                "text": "Sample document text",
                "embedding": [0.1, 0.2, 0.3],
                "header": "SampleHeader"
            }
        }
    ]]
    # Configure the mock to return our simulated search result
    mock_milvus_client.search.return_value = mock_search_result
    retriever = MilvusForSentenceDataRetriever(milvus_retriever_config)
    result = retriever.select(mock_collection, "sample query")
    assert result.status == "success"
    assert result.elements is not None
    assert len(result.elements) == 1
    assert result.elements[0]["text"] == "Sample document text"
    # Ensure the mock was called with the expected arguments
    mock_milvus_client.search.assert_called_once()


@patch('src.lib.services.rag.data_retrievers.milvus.sentences.Logger.get_logger')
@patch('pymilvus.MilvusClient')
def test_select_exception_handling(mock_milvus_client, mock_get_logger, milvus_retriever_config):  # pylint: disable=W0621
    """
    Test the select method to ensure it handles exceptions during data retrieval correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    mock_collection = {
        "client": mock_milvus_client,
        "name": "test_milvus_collection"
    }
    # Force the mock client to raise an exception on search
    mock_milvus_client.search.side_effect = Exception("Retrieval error")
    retriever = MilvusForSentenceDataRetriever(milvus_retriever_config)
    result = retriever.select(mock_collection, "sample query")
    assert result.status == "failure"
    assert "An error occurred while retrieving data" in result.error_message


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
