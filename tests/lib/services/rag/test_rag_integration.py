#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration test for DataStorage, DataLoader, and DataRetriever components in the RAG system.

This test verifies that:
1. A data collection can be retrieved or created.
2. Documents can be inserted into the collection.
3. The relevant data can be retrieved based on a query.

To run this test, use:
    pytest -m "integration and rag"
"""

import os
import time
import pytest
from pymilvus import model
from athon.rag import DataStorage, DataLoader, DataRetriever


# --------------------------------
# Common sample elements to insert
# --------------------------------
ELEMENTS = [
    {
        'text': 'How to Bake the Perfect Sourdough Bread',
        'metadata': {'author': 'Chef John', 'topic': 'Cooking'}
    },
    {
        'text': 'The Impact of Climate Change on Coastal Ecosystems',
        'metadata': {'author': 'Dr. Emily Green', 'topic': 'Environmental Science'}
    },
    {
        'text': "Exploring Quantum Computing: A Beginner's Guide",
        'metadata': {'author': 'Alice Zhang', 'topic': 'Technology'}
    },
    {
        'text': 'The Rise and Fall of Ancient Rome: A Historical Overview',
        'metadata': {'author': 'Prof. Marcus Taylor', 'topic': 'History'}
    },
    {
        'text': '10 Yoga Poses for Beginners to Improve Flexibility',
        'metadata': {'author': 'Sarah Miller', 'topic': 'Fitness'}
    },
    {
        'text': 'Understanding Cryptocurrency: The Future of Finance',
        'metadata': {'author': 'David Lee', 'topic': 'Finance'}
    },
    {
        'text': 'The Psychology of Motivation and Goal Setting',
        'metadata': {'author': 'Dr. Jennifer Adams', 'topic': 'Psychology'}
    },
    {
        'text': 'How to Create Stunning Landscape Photography',
        'metadata': {'author': 'Michael Peters', 'topic': 'Photography'}
    },
    {
        'text': 'The Science Behind Vaccines and Immunization',
        'metadata': {'author': 'Dr. Olivia Rivera', 'topic': 'Medicine'}
    },
    {
        'text': 'Introduction to Machine Learning Algorithms',
        'metadata': {'author': 'James Smith', 'topic': 'Artificial Intelligence'}
    }
]


# --------------------------------------
# 1) CHROMA INTEGRATION TEST
# --------------------------------------
CHROMA_STORAGE_CONFIG = {
    'type': 'ChromaCollection',
    'path': 'tests/lib/services/rag/data',  # Adjust path as needed
    'collection': 'IntegrationTestsChroma',
    'reset': True,
}
CHROMA_LOADER_CONFIG = {
    'type': 'ChromaForSentences'
}
CHROMA_RETRIEVER_CONFIG = {
    'type': 'ChromaForSentences',
    'n_results': 3,
    'expansion_type': 'None',
}

@pytest.mark.integration
@pytest.mark.rag
def test_data_storage_workflow_chroma():
    """
    Test the full workflow (Chroma):
        - create/retrieve a data collection
        - insert data
        - retrieve relevant data
    """
    # 1) Storage
    data_storage = DataStorage.create(CHROMA_STORAGE_CONFIG)
    result = data_storage.get_collection()
    assert result.status == "success", (
        f"Failed to retrieve Chroma collection: {result.error_message}")
    collection = result.collection
    assert collection is not None, "Chroma collection should not be None after retrieval"
    # 2) Loader
    data_loader = DataLoader.create(CHROMA_LOADER_CONFIG)
    result = data_loader.insert(collection, ELEMENTS)
    assert result.status == "success", f"Failed to insert elements (Chroma): {result.error_message}"
    # 3) Retriever
    data_retriever = DataRetriever.create(CHROMA_RETRIEVER_CONFIG)
    query = "Info about photography?"
    result = data_retriever.select(collection, query)
    assert result.status == "success", (
        f"Failed to retrieve relevant data (Chroma): {result.error_message}")
    assert len(result.elements) > 0, "No elements retrieved (Chroma) for the query"
    element = result.elements[0]
    print(f"[Chroma] TEXT:\n{element['text']}\nMETADATA:\n{element['metadata']}\n")
    assert "Photography" in element['metadata'].get('topic', ""), \
        f"Expected topic 'Photography' (Chroma), got: {element['metadata'].get('topic', '')}"


# --------------------------------------
# 2) MILVUS INTEGRATION TEST
# --------------------------------------
EMBEDDING_FUNCTION = model.DefaultEmbeddingFunction()
MILVUS_STORAGE_CONFIG = {
    'type': 'MilvusCollection',
    'path': 'tests/lib/services/rag/data/milvus.db',
    'collection': 'IntegrationTestsMilvus',
    'reset': True,
}
MILVUS_LOADER_CONFIG = {
    'type': 'MilvusForSentences'
}
MILVUS_RETRIEVER_CONFIG = {
    'type': 'MilvusForSentences',
    'embedding_function': EMBEDDING_FUNCTION,
    'n_results': 3,
    'output_fields': ['text', 'embedding', 'author', 'topic']
}

@pytest.mark.integration
@pytest.mark.rag
def test_data_storage_workflow_milvus():
    """
    Test the full workflow (Milvus):
        - create/retrieve a data collection
        - insert data
        - retrieve relevant data
    """
    # 1) Storage
    data_storage = DataStorage.create(MILVUS_STORAGE_CONFIG)
    result = data_storage.get_collection()
    assert result.status == "success", (
        f"Failed to retrieve Milvus collection: {result.error_message}")
    collection = result.collection
    assert collection is not None, "Milvus collection should not be None after retrieval"
    # 2) Loader
    texts = [elem["text"] for elem in ELEMENTS]  # Extract just the text for embedding
    embeddings = EMBEDDING_FUNCTION.encode_documents(texts)
    for elem, emb in zip(ELEMENTS, embeddings):
        # We store the embedding vector inside the 'metadata' dict
        elem["metadata"]["embedding"] = emb
    data_loader = DataLoader.create(MILVUS_LOADER_CONFIG)
    result = data_loader.insert(collection, ELEMENTS)
    assert result.status == "success", f"Failed to insert elements (Milvus): {result.error_message}"
    # 3) Retriever
    time.sleep(5)
    data_retriever = DataRetriever.create(MILVUS_RETRIEVER_CONFIG)
    query = "Info about photography?"
    result = data_retriever.select(collection, query)
    assert result.status == "success", (
        f"Failed to retrieve relevant data (Milvus): {result.error_message}")
    assert len(result.elements) > 0, "No elements retrieved (Milvus) for the query"
    element = result.elements[0]
    print(f"[Milvus] TEXT:\n{element['text']}\nMETADATA:\n{element['metadata']}\n")
    assert "Photography" in element['metadata'].get('topic', ""), \
        f"Expected topic 'Photography' (Milvus), got: {element['metadata'].get('topic', '')}"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    # Run only tests marked with 'integration' and 'rag' in this file
    pytest.main([current_file, '-vv', '-m', 'integration and rag'])
