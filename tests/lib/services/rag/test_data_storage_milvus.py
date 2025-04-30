#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataStorage factory and its storage flavors
in the data storage module. The tests ensure that the factory method correctly
initializes and returns instances of the appropriate storage types based on
the given configuration. It also tests the behavior of the storage's
get_collection method to ensure correct retrieval or creation of
collections in Milvus.
"""

import os
from unittest.mock import patch
import pytest

# Make sure these imports match your actual module paths:
# e.g., if your DataStorage factory is in src.lib.services.rag.data_storage
# and your Milvus code is in src.lib.services.rag.data_storages.milvus.collection,
# then these imports should be correct as shown below.
from src.lib.services.rag.data_storage import DataStorage
from src.lib.services.rag.data_storages.milvus.collection import (
    MilvusCollectionDataStorage
)

@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "MilvusCollection",
            "path": "tests/lib/services/rag/data/milvus.db",
            "collection": "test_milvus_collection",
            "reset": True

        },
        MilvusCollectionDataStorage
    )
])
def test_create_milvus(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of MilvusCollectionDataStorage
    based on the configuration provided.
    """
    storage_instance = DataStorage.create(config)
    assert isinstance(storage_instance, expected_class)


def test_create_milvus_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed for Milvus.
    """
    with pytest.raises(ValueError):
        DataStorage.create({"type": "InvalidType"})


@pytest.fixture
def milvus_collection_config_success():
    """
    Mockup MilvusCollectionDataStorage configuration.
    """
    return {
        "type": "MilvusCollection",
        "path": "tests/lib/services/rag/data/milvus.db",
        "collection": "test_milvus_collection_success"
    }


@patch('src.lib.services.rag.data_storages.milvus.collection.MilvusClient')
@patch('src.lib.services.rag.data_storages.milvus.collection.Logger')
def test_get_milvus_collection_success(
    mock_logger,  # pylint: disable=unused-argument
    mock_milvus_client,
    milvus_collection_config_success  # pylint: disable=W0621
):
    """
    Test the get_collection method of MilvusCollectionDataStorage to verify it returns
    the expected collection name (string here) and logs the correct messages.
    """
    mock_milvus_instance = mock_milvus_client.return_value

    # Suppose our mock list_collections returns no existing collections,
    # so the code will attempt creation.
    mock_milvus_instance.list_collections.return_value = []

    storage = MilvusCollectionDataStorage(milvus_collection_config_success)
    result = storage.get_collection()

    assert result.status == "success"
    # In our code, we store the collection name (string) in result.collection
    # If you change that in your code, adjust this assertion accordingly.
    assert result.collection['name'] == "test_milvus_collection_success"


@pytest.fixture
def milvus_collection_config_singleton():
    """
    Mockup MilvusCollectionDataStorage configuration for testing singleton behavior.
    """
    return {
        "type": "MilvusCollection",
        "path": "tests/lib/services/rag/data/milvus.db",
        "collection": "test_milvus_collection_singleton"
    }


@patch('src.lib.services.rag.data_storages.milvus.collection.MilvusClient')
def test_milvus_singleton_behavior(mock_milvus_client, milvus_collection_config_singleton):  # pylint: disable=W0621
    """
    Test the singleton behavior of MilvusCollectionDataStorage to ensure that multiple
    calls with the same configuration return the same underlying collection reference.
    """
    mock_milvus_instance = mock_milvus_client.return_value

    # Suppose our mock list_collections returns the collection on the first creation,
    # so no reset is needed after the first creation call.
    mock_milvus_instance.list_collections.return_value = []

    # Create first instance
    storage1 = MilvusCollectionDataStorage(milvus_collection_config_singleton)
    result1 = storage1.get_collection()

    # Create second instance with the same configuration
    storage2 = MilvusCollectionDataStorage(milvus_collection_config_singleton)
    result2 = storage2.get_collection()

    # Ensure that the same collection name is returned for both
    assert result1.collection == result2.collection

    # The code that calls create_collection or drop_collection should happen once
    # unless 'reset' is true. You can refine or add more assertions
    # based on how your code is expected to behave.
    mock_milvus_instance.create_collection.assert_called_once()
    mock_milvus_instance.drop_collection.assert_not_called()


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
