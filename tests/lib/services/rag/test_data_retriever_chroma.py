#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataRetriever factory and the ChromaForSentenceDataRetriever class.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate retriever types based on the given configuration. It also tests the behavior of 
the retriever's select method to ensure correct data retrieval and processing.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from src.lib.services.rag.data_retriever import DataRetriever
from src.lib.services.rag.data_retrievers.chroma.sentences import (
    ChromaForSentenceDataRetriever)


@pytest.mark.parametrize("config, expected_class", [
    (
        {"type": "ChromaForSentences"},
        ChromaForSentenceDataRetriever
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
def chroma_retriever_config():
    """
    Fixture to provide a mock configuration for ChromaForSentenceDataRetriever.
    """
    return {
        "type": "ChromaForSentences",
        "include": ["documents", "metadatas"],
        "n_results": 5,
        "expansion_type": "Section",
        "sentence_window": 3,
        "max_plot": 1000
    }


@patch('src.lib.services.rag.data_retrievers.chroma.sentences.Logger.get_logger')
def test_select_success(mock_get_logger, chroma_retriever_config):  # pylint: disable=W0621
    """
    Test the select method to ensure it successfully retrieves
    data from Chroma and processes it correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock Chroma collection behavior
    mock_collection = MagicMock()
    mock_query_result = {
        'documents': [["Sample document text"]],
        'metadatas': [[{"header": "Sample Header"}]],
        'ids': [["0"]],
    }
    mock_collection.query.return_value = mock_query_result
    retriever = ChromaForSentenceDataRetriever(chroma_retriever_config)
    result = retriever.select(mock_collection, "sample query")
    assert result.status == "success"
    assert result.elements is not None
    mock_collection.query.assert_called_once_with(
        query_texts=["sample query"],
        n_results=chroma_retriever_config["n_results"],
        include=chroma_retriever_config["include"]
    )


@patch('src.lib.services.rag.data_retrievers.chroma.sentences.Logger.get_logger')
def test_select_exception_handling(mock_get_logger, chroma_retriever_config):  # pylint: disable=W0621
    """
    Test the select method to ensure it handles exceptions during data retrieval correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock an exception during retrieval
    mock_collection = MagicMock()
    mock_collection.query.side_effect = Exception("Retrieval error")
    retriever = ChromaForSentenceDataRetriever(chroma_retriever_config)
    result = retriever.select(mock_collection, "sample query")
    assert result.status == "failure"
    assert "An error occurred while retrieving data" in result.error_message


@patch('src.lib.services.rag.data_retrievers.chroma.sentences.Logger.get_logger')
def test_expand_with_section_window(mock_get_logger, chroma_retriever_config):  # pylint: disable=W0621
    """
    Test the _expand_with_section_window method to ensure it expands results correctly by section.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock Chroma collection behavior
    mock_collection = MagicMock()
    mock_query_result = {
        'documents': [["Sample document text"]],
        'metadatas': [[{"header": "Sample Header"}]],
        'ids': [["0"]],
    }
    mock_collection.query.return_value = mock_query_result
    mock_collection.get.return_value = {
        'ids': ["0", "1"],
        'documents': ["First section text", "Second section text"]
    }
    retriever = ChromaForSentenceDataRetriever(chroma_retriever_config)
    expanded_result = retriever._expand_with_section_window(mock_collection, mock_query_result)  # pylint: disable=W0212
    assert "First section text Second section text" in expanded_result['documents'][0][0]
    mock_collection.get.assert_called_once_with(
        where={"header": "Sample Header"},
        include=["documents"]
    )


@patch('src.lib.services.rag.data_retrievers.chroma.sentences.Logger.get_logger')
def test_expand_with_sentence_window(mock_get_logger, chroma_retriever_config):  # pylint: disable=W0621
    """
    Test the _expand_with_sentence_window method to ensure
    it expands results correctly by sentence window.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock Chroma collection behavior
    mock_collection = MagicMock()
    mock_query_result = {
        'documents': [["Sample document text"]],
        'metadatas': [[{"header": "Sample Header"}]],
        'ids': [["0"]],
    }
    mock_collection.query.return_value = mock_query_result
    mock_collection.count.return_value = 100  # Mock the count of documents
    # Mock the behavior of `get` method for expanding by sentence window
    mock_collection.get.return_value = {
        'ids': ["0", "1", "2"],
        'documents': ["Sentence one", "Sentence two", "Sentence three"]
    }
    retriever = ChromaForSentenceDataRetriever(chroma_retriever_config)
    # Ensure _create_id_vector works as expected by controlling the return values
    with patch.object(retriever, '_create_id_vector', return_value=["0", "1", "2"]):
        expanded_result = retriever._expand_with_sentence_window(mock_collection, mock_query_result)  # pylint: disable=W0212
    assert "Sentence one Sentence two Sentence three" in expanded_result['documents'][0][0]
    mock_collection.get.assert_called_once_with(
        ids=['0', '1', '2'],
        include=["documents"]
    )


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
