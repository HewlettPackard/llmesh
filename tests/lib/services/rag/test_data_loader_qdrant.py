#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataLoader factory and its loader flavor,
QdrantForSentenceDataLoader, in the data loading module.
The tests ensure that the factory method correctly initializes and returns 
instances of the appropriate loader types based on the given configuration.
It also tests the specific behavior of the loader's methods to ensure correct
setup and functionality.
"""

import os
from unittest.mock import MagicMock, patch
import pytest
from src.lib.services.rag.data_loader import DataLoader
from src.lib.services.rag.data_loaders.qdrant.sentences import (
    QdrantForSentenceDataLoader)


@pytest.mark.parametrize("config, expected_class", [
    (
        {"type": "QdrantForSentences"},
        QdrantForSentenceDataLoader
    )
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    loader_instance = DataLoader.create(config)
    assert isinstance(loader_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        DataLoader.create({"type": "InvalidType"})


@pytest.fixture
def qdrant_for_sentences_config():
    """
    Mockup QdrantForSentenceDataLoader configuration.
    """
    return {
        "type": "QdrantForSentences"
    }


@patch('src.lib.services.core.log.Logger')
@patch('qdrant_client.QdrantClient')
def test_insert_success(mock_qdrant_client, mock_logger, qdrant_for_sentences_config):  # pylint: disable=W0621, W0613
    """
    Test the insert method of QdrantForSentenceDataLoader to verify
    it performs successful data insertion.
    """
    # Create a mock response for the count method
    mock_count_response = MagicMock()
    mock_count_response.count = 0  # Set the count value to 0
    # Mock the return value of the count method on the Qdrant client
    mock_qdrant_client.count.return_value = mock_count_response
    # Mock the client and its collection
    mock_collection = {"client": mock_qdrant_client, "name": "test_collection"}
    # Initialize the loader
    loader = QdrantForSentenceDataLoader(qdrant_for_sentences_config)
    # Create mock elements
    elements = [
        {'text': 'Document 1', 'metadata': {'author': 'Author 1', 'embedding': [0.1, 0.2, 0.3]}},
        {'text': 'Document 2', 'metadata': {'author': 'Author 2', 'embedding': [0.4, 0.5, 0.6]}}
    ]
    # Call the insert method
    result = loader.insert(mock_collection, elements)
    # Assertions
    assert result.status == "success"
    mock_qdrant_client.upsert.assert_called_once()


@patch('src.lib.services.core.log.Logger')
@patch('qdrant_client.QdrantClient')
def test_insert_failure(mock_qdrant_client, mock_logger, qdrant_for_sentences_config):  # pylint: disable=W0621, W0613
    """
    Test the insert method of QdrantForSentenceDataLoader
    to ensure it handles insertion errors gracefully.
    """
    mock_collection = {"client": mock_qdrant_client, "name": "test_collection"}
    mock_qdrant_client.upsert.side_effect = Exception("Insertion error")
    loader = QdrantForSentenceDataLoader(qdrant_for_sentences_config)
    elements = [
        {'text': 'Document 1', 'metadata': {'author': 'Author 1', 'embedding': [0.1, 0.2, 0.3]}}
    ]
    result = loader.insert(mock_collection, elements)
    assert result.status == "failure"
    assert "An error occurred while inserting data" in result.error_message


def test_convert_to_documents(qdrant_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _convert_to_documents method to verify
    it correctly splits elements into documents, metadata, and embeddings.
    """
    loader = QdrantForSentenceDataLoader(qdrant_for_sentences_config)
    elements = [
        {'text': 'Document 1', 'metadata': {'author': 'Author 1', 'embedding': [0.1, 0.2, 0.3]}},
        {'text': 'Document 2', 'metadata': {'author': 'Author 2', 'embedding': [0.4, 0.5, 0.6]}}
    ]
    documents, metadatas, embeddings = loader._convert_to_documents(elements)  # pylint: disable=W0212
    assert documents == ['Document 1', 'Document 2']
    assert metadatas == [{'author': 'Author 1'}, {'author': 'Author 2'}]
    assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_convert_to_documents_invalid_embedding(qdrant_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _convert_to_documents method to verify it raises a ValueError 
    when the embedding is missing or invalid.
    """
    loader = QdrantForSentenceDataLoader(qdrant_for_sentences_config)
    elements = [
        {'text': 'Document 1', 'metadata': {'author': 'Author 1', 'embedding': None}},
        {'text': 'Document 2', 'metadata': {'author': 'Author 2', 'embedding': "invalid_embedding"}}
    ]
    with pytest.raises(ValueError, match="Invalid or missing embedding"):
        loader._convert_to_documents(elements)  # pylint: disable=W0212


@patch('qdrant_client.QdrantClient')
def test_insert_documents_into_collection(mock_qdrant_client, qdrant_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _insert_documents_into_collection method to verify it correctly inserts documents 
    and metadata into the Qdrant collection.
    """
    # Create a mock response for the count method
    mock_count_response = MagicMock()
    mock_count_response.count = 0  # Set the count value to 0
    # Mock the return value of the count method on the Qdrant client
    mock_qdrant_client.count.return_value = mock_count_response
    loader = QdrantForSentenceDataLoader(qdrant_for_sentences_config)
    mock_collection = {"client": mock_qdrant_client, "name": "test_collection"}
    documents = ['Document 1', 'Document 2']
    metadatas = [{'author': 'Author 1'}, {'author': 'Author 2'}]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    # Simulate initial document count in the collection
    mock_qdrant_client.collection_name.count.return_value = 0
    # Test inserting documents
    loader._insert_documents_into_collection(mock_collection, embeddings, documents, metadatas)  # pylint: disable=W0212
    # Check that upsert was called with correct arguments
    mock_qdrant_client.upsert.assert_called_once()


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
