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
from src.lib.services.rag.data_storage import DataStorage
from src.lib.services.rag.data_storages.chroma.collection import (
    ChromaCollectionDataStorage)


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "ChromaCollection",
            "path": "self_serve_platform/tests/unit/data",
            "collection": "test_collection1"
        },
        ChromaCollectionDataStorage
    )
])
def test_create_chroma(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of ChromaCollectionDataStorage
    based on the configuration provided.
    """
    storage_instance = DataStorage.create(config)
    assert isinstance(storage_instance, expected_class)


def test_create_chroma_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed for Chroma.
    """
    with pytest.raises(ValueError):
        DataStorage.create({"type": "InvalidType"})


@pytest.fixture
def chroma_collection_config_success():
    """
    Mockup ChromaCollectionDataStorage configuration.
    """
    return {
        "type": "ChromaCollection",
        "path": "self_serve_platform/tests/unit/data",
        "collection": "test_collection2"
    }


@patch('src.lib.services.rag.data_storages.chroma.collection.PersistentClient')
@patch('src.lib.services.rag.data_storages.chroma.collection.Logger')
def test_get_chroma_collection_success(
        mock_logger,  # pylint: disable=W0613
        mock_persistent_client, chroma_collection_config_success):  # pylint: disable=W0621
    """
    Test the get_collection method of ChromaCollectionDataStorage to verify it returns
    the expected collection and logs the correct messages.
    """
    mock_client_instance = mock_persistent_client.return_value
    mock_collection = MagicMock()
    mock_client_instance.get_or_create_collection.return_value = mock_collection
    storage = ChromaCollectionDataStorage(chroma_collection_config_success)
    result = storage.get_collection()
    assert result.status == "success"
    assert result.collection == mock_collection


@pytest.fixture
def chroma_collection_config_singleton():
    """
    Mockup ChromaCollectionDataStorage configuration.
    """
    return {
        "type": "ChromaCollection",
        "path": "self_serve_platform/tests/unit/data",
        "collection": "test_collection3"
    }


@patch('src.lib.services.rag.data_storages.chroma.collection.PersistentClient')
def test_chroma_singleton_behavior(mock_persistent_client, chroma_collection_config_singleton):  # pylint: disable=W0621
    """
    Test the singleton behavior of ChromaCollectionDataStorage to ensure that multiple
    calls with the same configuration return the same instance.
    """
    mock_client_instance = mock_persistent_client.return_value
    mock_collection = MagicMock()
    mock_client_instance.get_or_create_collection.return_value = mock_collection
    # Create first instance
    storage1 = ChromaCollectionDataStorage(chroma_collection_config_singleton)
    result1 = storage1.get_collection()
    # Create second instance with the same configuration
    storage2 = ChromaCollectionDataStorage(chroma_collection_config_singleton)
    result2 = storage2.get_collection()
    # Ensure that the same collection instance is returned for both
    assert result1.collection is result2.collection
    mock_client_instance.get_or_create_collection.assert_called_once()


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
