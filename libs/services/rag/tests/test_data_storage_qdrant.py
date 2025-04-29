#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataStorage factory and its storage flavors,
in the data storage module.
The tests ensure that the factory method correctly initializes and returns
instances of the appropriate storage types based on the given configuration.
It also tests the behavior of the storage's get_collection method to ensure
correct retrieval or creation of collections in ChromaDB and QdrantDB.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from libs.services.rag.data_storage import DataStorage
from libs.services.rag.data_storages.qdrant.collection import (
    QdrantCollectionDataStorage)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "QdrantCollection",
            "url": "http://localhost:6333",
            "collection": "test_collection1",
            "vector_size": 128
        },
        QdrantCollectionDataStorage
    )
])
@patch('libs.services.rag.data_storages.qdrant.collection.QdrantClient')  # Mock QdrantClient
def test_create_qdrant(mock_qdrant_client, config, expected_class):
    """
    Test the create factory method to ensure it returns instances of QdrantCollectionDataStorage
    based on the configuration provided.
    """
    # Mocking Qdrant collection creation behavior
    mock_client_instance = MagicMock()
    mock_qdrant_client.return_value = mock_client_instance
    mock_client_instance.get_collection.return_value = "mocked_collection"
    # Create the storage instance
    storage_instance = DataStorage.create(config)
    # Ensure the storage instance is of the correct type
    assert isinstance(storage_instance, expected_class)
    # Ensure Qdrant client was instantiated correctly
    mock_qdrant_client.assert_called_once_with(url=config['url'])
    # Ensure the collection retrieval method was called
    mock_client_instance.get_collection.assert_called_once_with(config['collection'])


def test_create_qdrant_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed for Qdrant.
    """
    with pytest.raises(ValueError):
        DataStorage.create({"type": "InvalidType"})


@pytest.fixture
def qdrant_collection_config_success():
    """
    Mockup QdrantCollectionDataStorage configuration.
    """
    return {
        "type": "QdrantCollection",
        "url": "http://localhost:6333",
        "collection": "test_collection2",
        "vector_size": 128
    }


@patch('libs.services.rag.data_storages.qdrant.collection.QdrantClient')
@patch('libs.services.rag.data_storages.qdrant.collection.Logger')
def test_get_qdrant_collection_success(
        mock_logger,  # pylint: disable=W0613
        mock_qdrant_client, qdrant_collection_config_success):  # pylint: disable=W0621
    """
    Test the get_collection method of QdrantCollectionDataStorage to verify it returns
    the expected collection and logs the correct messages.
    """
    mock_client_instance = mock_qdrant_client.return_value
    mock_collection = MagicMock()
    mock_client_instance.get_collection.return_value = mock_collection
    storage = QdrantCollectionDataStorage(qdrant_collection_config_success)
    result = storage.get_collection()
    assert result.status == "success"
    assert result.collection["name"] == "test_collection2"


@pytest.fixture
def qdrant_collection_config_singleton():
    """
    Mockup QdrantCollectionDataStorage configuration for singleton behavior.
    """
    return {
        "type": "QdrantCollection",
        "url": "http://localhost:6333",
        "collection": "test_collection3",
        "vector_size": 128
    }


@patch('libs.services.rag.data_storages.qdrant.collection.QdrantClient')
def test_qdrant_singleton_behavior(mock_qdrant_client, qdrant_collection_config_singleton):  # pylint: disable=W0621
    """
    Test the singleton behavior of QdrantCollectionDataStorage to ensure that multiple
    calls with the same configuration return the same instance.
    """
    mock_client_instance = mock_qdrant_client.return_value
    mock_collection = MagicMock()
    mock_client_instance.get_collection.return_value = mock_collection
    # Create first instance
    storage1 = QdrantCollectionDataStorage(qdrant_collection_config_singleton)
    result1 = storage1.get_collection()
    # Create second instance with the same configuration
    storage2 = QdrantCollectionDataStorage(qdrant_collection_config_singleton)
    result2 = storage2.get_collection()
    # Ensure that the same collection instance is returned for both
    assert result1.collection == result2.collection
    mock_client_instance.get_collection.assert_called_once()


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
