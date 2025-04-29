#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataRetriever factory and the QdrantForSentenceDataRetriever class.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate retriever types based on the given configuration. It also tests the behavior of 
the retriever's select method to ensure correct data retrieval and processing.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from libs.services.rag.data_retriever import DataRetriever
from libs.services.rag.data_retrievers.qdrant.sentences import (
    QdrantForSentenceDataRetriever)


@pytest.mark.parametrize("config, expected_class", [
    (
        {"type": "QdrantForSentences", "embedding_function": MagicMock()},
        QdrantForSentenceDataRetriever
    )
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
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
def qdrant_retriever_config():
    """
    Fixture to provide a mock configuration for QdrantForSentenceDataRetriever.
    """
    return {
        "type": "QdrantForSentences",
        "embedding_function": MagicMock(),
        "n_results": 5,
        "expansion_type": "Section",
        "sentence_window": 3,
    }


@patch('libs.services.rag.data_retrievers.qdrant.sentences.Logger.get_logger')
@patch('qdrant_client.QdrantClient')
def test_select_success(mock_qdrant_client, mock_get_logger, qdrant_retriever_config):  # pylint: disable=W0621
    """
    Test the select method to ensure it successfully retrieves
    data from Qdrant and processes it correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock Qdrant collection behavior
    mock_collection = {
        "client": mock_qdrant_client,
        "name": "test_collection"
    }
    mock_query_result = [
        MagicMock(
            payload={"header": "Sample Header", "text": "Sample document text"},
            score=0.9,
            vector=[0.1, 0.2])
    ]
    mock_qdrant_client.search.return_value = mock_query_result
    retriever = QdrantForSentenceDataRetriever(qdrant_retriever_config)
    result = retriever.select(mock_collection, "sample query")
    assert result.status == "success"
    assert result.elements is not None
    mock_qdrant_client.search.assert_called_once()


@patch('libs.services.rag.data_retrievers.qdrant.sentences.Logger.get_logger')
@patch('qdrant_client.QdrantClient')
def test_select_exception_handling(mock_qdrant_client, mock_get_logger, qdrant_retriever_config):  # pylint: disable=W0621
    """
    Test the select method to ensure it handles exceptions during data retrieval correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock an exception during retrieval
    mock_collection = {
        "client": mock_qdrant_client,
        "name": "test_collection"
    }
    mock_qdrant_client.search.side_effect = Exception("Retrieval error")
    retriever = QdrantForSentenceDataRetriever(qdrant_retriever_config)
    result = retriever.select(mock_collection, "sample query")
    assert result.status == "failure"
    assert "An error occurred while retrieving data" in result.error_message


@patch('libs.services.rag.data_retrievers.qdrant.sentences.Logger.get_logger')
@patch('qdrant_client.QdrantClient')
def test_expand_with_section_window(mock_qdrant_client, mock_get_logger, qdrant_retriever_config):  # pylint: disable=W0621
    """
    Test the _expand_with_section_window method to ensure it expands results correctly by section.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock Qdrant collection behavior
    mock_collection = {
        "client": mock_qdrant_client,
        "name": "test_collection"
    }
    mock_query_result = [
        MagicMock(
            payload={"header": "Sample Header", "documents": "Sample document text"},
            score=0.9)
    ]
    mock_section_result = [
        MagicMock(id="0", payload={"documents": "First section text"}),
        MagicMock(id="1", payload={"documents": "Second section text"})
    ]
    mock_qdrant_client.scroll.return_value = mock_section_result
    retriever = QdrantForSentenceDataRetriever(qdrant_retriever_config)
    expanded_result = retriever._expand_with_section_window(mock_collection, mock_query_result)  # pylint: disable=W0212
    assert "First section text Second section text" in expanded_result[0].payload["documents"]
    mock_qdrant_client.scroll.assert_called_once()


@patch('libs.services.rag.data_retrievers.qdrant.sentences.Logger.get_logger')
@patch('qdrant_client.QdrantClient')
def test_expand_with_sentence_window(mock_qdrant_client, mock_get_logger, qdrant_retriever_config):  # pylint: disable=W0621
    """
    Test the _expand_with_sentence_window method to ensure
    it expands results correctly by sentence window.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock Qdrant collection behavior
    mock_collection = {
        "client": mock_qdrant_client,
        "name": "test_collection"
    }
    mock_query_result = [
        MagicMock(
            payload={"header": "Sample Header", "documents": "Sample document text"},
            score=0.9)
    ]
    mock_qdrant_client.count.return_value = MagicMock(count=100)  # Mock the count of documents
    # Mock the behavior of `scroll` method for expanding by sentence window
    mock_sentence_result = [
        MagicMock(id="0", payload={"documents": "Sentence one"}),
        MagicMock(id="1", payload={"documents": "Sentence two"}),
        MagicMock(id="2", payload={"documents": "Sentence three"})
    ]
    mock_qdrant_client.scroll.return_value = mock_sentence_result
    retriever = QdrantForSentenceDataRetriever(qdrant_retriever_config)
    # Ensure _create_id_vector works as expected by controlling the return values
    with patch.object(retriever, '_create_id_vector', return_value=["0", "1", "2"]):
        expanded_result = retriever._expand_with_sentence_window(mock_collection, mock_query_result)  # pylint: disable=W0212
    assert "Sentence one Sentence two Sentence three" in expanded_result[0].payload["documents"]
    mock_qdrant_client.scroll.assert_called_once()


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
