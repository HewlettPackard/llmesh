#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pytest suite for the RAG (Retrieval-Augmented Generation) service.

This test suite verifies:
- Document loading into the vector store
- RAG query returns valid content
- Augmentation and reranking behaviors
- Edge case handling (e.g., empty or nonsense queries)

Run with: pytest test_rag_service.py -vv
"""

import os
import pytest
from src.platform.rag.main import retrieve
from src.platform.rag.load import load_files


@pytest.mark.integration
@pytest.mark.rag
def test_rag_load_files():
    """Test that loading files completes without exception."""
    try:
        load_files(reset=True)
    except Exception as e:  # pylint: disable=W0718
        pytest.fail(f"load_files() raised an exception: {e}")


@pytest.mark.integration
@pytest.mark.rag
@pytest.mark.asyncio
@pytest.mark.parametrize("query", [
    "What are the key features of 5G compared to 4G?",
    "How does 5G enable low-latency applications like autonomous vehicles?",
    "What role does network slicing play in 5G architecture?"
])
async def test_rag_retrieve_with_rerank(query):
    """Test retrieve() with reranking enabled."""
    response = await retrieve(query=query, augmentation="expansion", rerank=True)
    assert isinstance(response, str)
    assert len(response.strip()) > 0
    assert "```json" in response or "Answer" in response  # expected structure


@pytest.mark.integration
@pytest.mark.rag
@pytest.mark.asyncio
async def test_rag_retrieve_without_rerank():
    """Test retrieve() with rerank disabled."""
    query = "What is the use of SD-WAN in LAT-Mesh?"
    response = await retrieve(query=query, augmentation="hyde", rerank=False)
    assert isinstance(response, str)
    assert len(response.strip()) > 0


@pytest.mark.integration
@pytest.mark.rag
@pytest.mark.asyncio
async def test_rag_retrieve_empty_query():
    """Test retrieve() with an empty query."""
    response = await retrieve(query="", augmentation="expansion", rerank=True)
    assert isinstance(response, str)
    assert len(response.strip()) > 0 or "error" in response.lower()


@pytest.mark.integration
@pytest.mark.rag
@pytest.mark.asyncio
async def test_rag_retrieve_nonsense_query():
    """Test retrieve() with a nonsensical query."""
    query = "asdfghjklqwertyuiopzxcvbnm"
    response = await retrieve(query=query, augmentation="hyde", rerank=True)
    assert isinstance(response, str)
    assert len(response.strip()) > 0  # LLM should still respond reasonably


@pytest.mark.integration
@pytest.mark.rag
@pytest.mark.asyncio
async def test_rag_retrieve_invalid_augmentation():
    """Test retrieve() with invalid augmentation fallback."""
    query = "What is microsegmentation?"
    response = await retrieve(query=query, augmentation="unknown_type", rerank=True)
    assert isinstance(response, str)
    assert len(response.strip()) > 0


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, "-vv", "-m", "integration and rag"])
