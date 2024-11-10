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
import pytest
from athon.rag import DataStorage, DataLoader, DataRetriever


# Define configurations for DataStorage, DataLoader, and DataRetriever
STORAGE_CONFIG = {
    'type': 'ChromaCollection',
    'path': 'self_serve_platform/tests/integration/data',
    'collection': 'IntegrationTests',
    'reset': True,
}
LOADER_CONFIG = {
    'type': 'ChromaForSentences'
}
RETRIEVER_CONFIG = {
    'type': 'ChromaForSentences',
    'n_results': 3,
    'expansion_type': 'None',
}
# Sample elements to insert into the collection
ELEMENTS = [
    {'text': 'How to Bake the Perfect Sourdough Bread',
    'metadata': {'author': 'Chef John', 'topic': 'Cooking'}},
    {'text': 'The Impact of Climate Change on Coastal Ecosystems',
    'metadata': {'author': 'Dr. Emily Green', 'topic': 'Environmental Science'}},
    {'text': 'Exploring Quantum Computing: A Beginner\'s Guide',
    'metadata': {'author': 'Alice Zhang', 'topic': 'Technology'}},
    {'text': 'The Rise and Fall of Ancient Rome: A Historical Overview',
    'metadata': {'author': 'Prof. Marcus Taylor', 'topic': 'History'}},
    {'text': '10 Yoga Poses for Beginners to Improve Flexibility',
    'metadata': {'author': 'Sarah Miller', 'topic': 'Fitness'}},
    {'text': 'Understanding Cryptocurrency: The Future of Finance',
    'metadata': {'author': 'David Lee', 'topic': 'Finance'}},
    {'text': 'The Psychology of Motivation and Goal Setting',
    'metadata': {'author': 'Dr. Jennifer Adams', 'topic': 'Psychology'}},
    {'text': 'How to Create Stunning Landscape Photography',
    'metadata': {'author': 'Michael Peters', 'topic': 'Photography'}},
    {'text': 'The Science Behind Vaccines and Immunization',
    'metadata': {'author': 'Dr. Olivia Rivera', 'topic': 'Medicine'}},
    {'text': 'Introduction to Machine Learning Algorithms',
    'metadata': {'author': 'James Smith', 'topic': 'Artificial Intelligence'}}
]


@pytest.mark.integration
@pytest.mark.rag
def test_data_storage_workflow():
    """
    Test the full workflow of creating a data collection, inserting data,
    and retrieving relevant data using the DataStorage, DataLoader, and DataRetriever.
    """
    # Initialize the Data Storage with the provided configuration
    data_storage = DataStorage.create(STORAGE_CONFIG)
    # Retrieve the data collection
    result = data_storage.get_collection()
    # Ensure the collection retrieval is successful
    assert result.status == "success", f"Failed to retrieve collection: {result.error_message}"
    collection = result.collection
    assert collection is not None, "Collection should not be None after retrieval"
    # Initialize the Data Loader with the provided configuration
    data_loader = DataLoader.create(LOADER_CONFIG)
    # Insert elements into the collection
    result = data_loader.insert(collection, ELEMENTS)
    # Ensure the insertion is successful
    assert result.status == "success", f"Failed to insert elements: {result.error_message}"
    # Initialize the Data Retriever with the provided configuration
    data_retriever = DataRetriever.create(RETRIEVER_CONFIG)
    # Example query to retrieve relevant data
    query = "Info about photography?"
    # Retrieve data based on the query
    result = data_retriever.select(collection, query)
    # Ensure the retrieval is successful
    assert result.status == "success", f"Failed to retrieve relevant data: {result.error_message}"
    assert len(result.elements) > 0, "No elements retrieved for the query"
    # Validate the contents of the retrieved data
    element = result.elements[0]
    print(f"TEXT:\n{element['text']}\nMETADATA:\n{element['metadata']}\n")
    assert "Photography" in element['metadata']['topic'], \
        f"Expected topic 'Photography', but got: {element['metadata']['topic']}"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv', '-m', 'integration and rag'])
