#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataLoader factory and its loader flavor,
MilvusForSentenceDataLoader, in the data loading module.
The tests ensure that the factory method correctly initializes and returns
instances of the appropriate loader types based on the given configuration.
It also tests the specific behavior of the loader's methods to ensure correct
setup and functionality.
"""

import os
from unittest.mock import patch
import pytest

# Make sure these imports match your actual codebase paths
from src.lib.services.rag.data_loader import DataLoader
from src.lib.services.rag.data_loaders.milvus.sentences import (
    MilvusForSentenceDataLoader
)


@pytest.mark.parametrize("config, expected_class", [
    (
        {"type": "MilvusForSentences"},
        MilvusForSentenceDataLoader
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
def milvus_for_sentences_config():
    """
    Mockup MilvusForSentenceDataLoader configuration.
    """
    return {
        "type": "MilvusForSentences"
    }


@patch('src.lib.services.core.log.Logger')
@patch('pymilvus.MilvusClient')
def test_insert_success(mock_milvus_client, mock_logger, milvus_for_sentences_config):  # pylint: disable=W0621, W0613
    """
    Test the insert method of MilvusForSentenceDataLoader to verify
    it performs successful data insertion.
    """
    # Mock the client and its collection
    mock_collection = {"client": mock_milvus_client, "name": "test_milvus_collection"}

    # Initialize the loader
    loader = MilvusForSentenceDataLoader(milvus_for_sentences_config)

    # Create mock elements
    elements = [
        {
            'text': 'Document 1',
            'metadata': {'author': 'Author 1', 'embedding': [0.1, 0.2, 0.3]}
        },
        {
            'text': 'Document 2',
            'metadata': {'author': 'Author 2', 'embedding': [0.4, 0.5, 0.6]}
        }
    ]

    # Call the insert method
    result = loader.insert(mock_collection, elements)

    # Assertions
    assert result.status == "success"
    mock_milvus_client.insert.assert_called_once()
    # We can also check that the call was made with the correct collection_name and data:
    assert mock_milvus_client.insert.call_args[1]["collection_name"] == "test_milvus_collection"
    inserted_data = mock_milvus_client.insert.call_args[1]["data"]
    assert len(inserted_data) == 2
    assert inserted_data[0]["text"] == "Document 1"
    assert inserted_data[1]["text"] == "Document 2"


@patch('src.lib.services.core.log.Logger')
@patch('pymilvus.MilvusClient')
def test_insert_failure(mock_milvus_client, mock_logger, milvus_for_sentences_config):  # pylint: disable=W0621, W0613
    """
    Test the insert method of MilvusForSentenceDataLoader
    to ensure it handles insertion errors gracefully.
    """
    # Cause an exception to be raised by mock insert
    mock_milvus_client.insert.side_effect = Exception("Insertion error")

    mock_collection = {"client": mock_milvus_client, "name": "test_milvus_collection"}

    loader = MilvusForSentenceDataLoader(milvus_for_sentences_config)
    elements = [
        {
            'text': 'Document 1',
            'metadata': {'author': 'Author 1', 'embedding': [0.1, 0.2, 0.3]}
        }
    ]
    result = loader.insert(mock_collection, elements)

    assert result.status == "failure"
    assert "An error occurred while inserting data" in result.error_message


def test_convert_to_documents(milvus_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _convert_to_documents method to verify
    it correctly splits elements into documents, metadata, and embeddings.
    """
    loader = MilvusForSentenceDataLoader(milvus_for_sentences_config)
    elements = [
        {
            'text': 'Document 1',
            'metadata': {'author': 'Author 1', 'embedding': [0.1, 0.2, 0.3]}
        },
        {
            'text': 'Document 2',
            'metadata': {'author': 'Author 2', 'embedding': [0.4, 0.5, 0.6]}
        }
    ]
    documents, metadatas, embeddings = loader._convert_to_documents(elements)  # pylint: disable=protected-access

    assert documents == ['Document 1', 'Document 2']
    # The embedding field is removed from metadata
    assert metadatas == [{'author': 'Author 1'}, {'author': 'Author 2'}]
    assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_convert_to_documents_invalid_embedding(milvus_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _convert_to_documents method to verify it raises a ValueError 
    when the embedding is missing or invalid.
    """
    loader = MilvusForSentenceDataLoader(milvus_for_sentences_config)
    elements = [
        {
            'text': 'Document 1',
            'metadata': {'author': 'Author 1', 'embedding': None}
        },
        {
            'text': 'Document 2',
            'metadata': {'author': 'Author 2', 'embedding': "invalid_embedding"}
        }
    ]
    with pytest.raises(ValueError, match="Invalid or missing embedding"):
        loader._convert_to_documents(elements)  # pylint: disable=protected-access


@patch('pymilvus.MilvusClient')
def test_insert_documents_into_collection(mock_milvus_client, milvus_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _insert_documents_into_collection method to verify it correctly inserts documents 
    and metadata into the Milvus collection.
    """
    loader = MilvusForSentenceDataLoader(milvus_for_sentences_config)
    mock_collection = {"client": mock_milvus_client, "name": "test_milvus_collection"}

    documents = ['Document 1', 'Document 2']
    metadatas = [{'author': 'Author 1'}, {'author': 'Author 2'}]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    loader._insert_documents_into_collection(  # pylint: disable=protected-access
        mock_collection,
        embeddings,
        documents,
        metadatas
    )

    # Check that insert was called with the correct arguments
    mock_milvus_client.insert.assert_called_once()
    inserted_args = mock_milvus_client.insert.call_args[1]
    assert inserted_args["collection_name"] == "test_milvus_collection"
    data = inserted_args["data"]
    assert len(data) == 2
    assert data[0]["text"] == "Document 1"
    assert data[0]["author"] == "Author 1"
    assert data[0]["embedding"] == [0.1, 0.2, 0.3]
    assert data[1]["text"] == "Document 2"
    assert data[1]["author"] == "Author 2"
    assert data[1]["embedding"] == [0.4, 0.5, 0.6]


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
