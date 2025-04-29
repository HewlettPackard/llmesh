#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataLoader factory and its loader flavor,
ChromaForSentenceDataLoader, in the data loading module.
The tests ensure that the factory method correctly initializes and returns 
instances of the appropriate loader types based on the given configuration.
It also tests the specific behavior of the loader's methods to ensure correct
setup and functionality.
"""

import os
from unittest.mock import MagicMock, patch
import pytest
from self_serve_platform.rag.data_loader import DataLoader
from self_serve_platform.rag.data_loaders.chroma_for_sentences import ChromaForSentenceDataLoader


@pytest.mark.parametrize("config, expected_class", [
    (
        {"type": "ChromaForSentences"},
        ChromaForSentenceDataLoader
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
def chroma_for_sentences_config():
    """
    Mockup ChromaForSentenceDataLoader configuration.
    """
    return {
        "type": "ChromaForSentences"
    }


@patch('self_serve_platform.rag.data_loaders.chroma_for_sentences.Logger')
def test_insert_success(mock_logger, chroma_for_sentences_config):  # pylint: disable=W0621, W0613
    """
    Test the insert method of ChromaForSentenceDataLoader to verify
    it performs successful data insertion.
    """
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    loader = ChromaForSentenceDataLoader(chroma_for_sentences_config)
    elements = [{'text': 'Document 1', 'metadata': {'author': 'Author 1'}},
                {'text': 'Document 2', 'metadata': {'author': 'Author 2'}}]
    result = loader.insert(mock_collection, elements)
    assert result.status == "success"
    mock_collection.add.assert_called_once()


@patch('self_serve_platform.rag.data_loaders.chroma_for_sentences.Logger')
def test_insert_failure(mock_logger, chroma_for_sentences_config):  # pylint: disable=W0621, W0613
    """
    Test the insert method of ChromaForSentenceDataLoader
    to ensure it handles insertion errors gracefully.
    """
    mock_collection = MagicMock()
    mock_collection.add.side_effect = Exception("Insertion error")
    loader = ChromaForSentenceDataLoader(chroma_for_sentences_config)
    elements = [{'text': 'Document 1', 'metadata': {'author': 'Author 1'}}]
    result = loader.insert(mock_collection, elements)
    assert result.status == "failure"
    assert "An error occurred while inserting data" in result.error_message


def test_convert_to_documents(chroma_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _convert_to_documents method to verify
    it correctly splits elements into documents and metadata.
    """
    loader = ChromaForSentenceDataLoader(chroma_for_sentences_config)
    elements = [{'text': 'Document 1', 'metadata': {'author': 'Author 1'}},
                {'text': 'Document 2', 'metadata': {'author': 'Author 2'}}]
    documents, metadatas = loader._convert_to_documents(elements)  # pylint: disable=W0212
    assert documents == ['Document 1', 'Document 2']
    assert metadatas == [{'author': 'Author 1'}, {'author': 'Author 2'}]


def test_convert_to_documents_invalid_metadata(chroma_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _convert_to_documents method to verify it correctly handles non-string metadata values.
    """
    loader = ChromaForSentenceDataLoader(chroma_for_sentences_config)
    elements = [{'text': 'Document 1', 'metadata': {'author': '123', 'tags': ['tag1', 'tag2']}}]
    documents, metadatas = loader._convert_to_documents(elements)  # pylint: disable=W0212
    assert documents == ['Document 1']
    assert metadatas == [{'author': '123', 'tags': "['tag1', 'tag2']"}]


def test_insert_documents_into_collection(chroma_for_sentences_config):  # pylint: disable=W0621
    """
    Test the _insert_documents_into_collection method to verify it correctly inserts documents 
    and metadata into the Chroma collection.
    """
    loader = ChromaForSentenceDataLoader(chroma_for_sentences_config)
    mock_collection = MagicMock()
    documents = ['Document 1', 'Document 2']
    metadatas = [{'author': 'Author 1'}, {'author': 'Author 2'}]
    mock_collection.count.return_value = 0
    loader._insert_documents_into_collection(mock_collection, documents, metadatas)  # pylint: disable=W0212
    mock_collection.add.assert_called_once_with(
        ids=['0', '1'],
        documents=documents,
        metadatas=metadatas
    )


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
