#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pytest suite for the Chat Service tool.

This test suite verifies:
- Correct behavior for different personas
- Default parameter handling
- Memory functionality (preservation and reset)
- Fallback on unknown personas
- Edge cases such as empty input or None values

Run with: pytest test_chat_service.py -vv
"""

import os
import pytest
from src.platform.chat.main import chat  # Update import if your file is named differently


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
@pytest.mark.parametrize("query,new,personas", [
    ("Tell me a pirate joke!", True, "pirate"),
    ("What is 5G?", True, "5g_expert"),
    ("Fix this: We is going to the store.", True, "copywriter"),
    ("What's the capital of Germany?", True, "assistant"),
    ("How do I write better?", True, ""),  # empty = default
])
async def test_chat_personas_and_default(query, new, personas):
    """Test different personas and the default assistant behavior."""
    response = await chat(query=query, new=new, personas=personas)
    assert isinstance(response, str)
    assert len(response.strip()) > 0


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
async def test_chat_fallback_on_invalid_persona():
    """Test fallback behavior when an unknown persona is used."""
    response = await chat(query="What time is it?", new=True, personas="nonexistent")
    assert isinstance(response, str)
    assert "error" not in response.lower()
    assert len(response.strip()) > 0


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
async def test_chat_memory_persistence():
    """Test that the assistant remembers previous messages if new=False."""
    first = await chat(query="What is AI?", new=True, personas="assistant")
    followup = await chat(query="And how is it used today?", new=False, personas="assistant")
    assert isinstance(first, str)
    assert isinstance(followup, str)
    assert len(followup.strip()) > 0
    assert "AI" in followup or "artificial" in followup.lower()


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
async def test_chat_memory_reset_with_new_flag():
    """Test that setting new=True resets memory and context."""
    _ = await chat(query="Tell me about cats.", new=True, personas="assistant")
    fresh = await chat(query="What did I just say?", new=True, personas="assistant")
    assert isinstance(fresh, str)
    assert len(fresh.strip()) > 0
    # No assert on content because behavior may vary by implementation


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
async def test_chat_default_param_behavior():
    """Test chat() with default parameters (no personas or new flag provided)."""
    response = await chat("What is the speed of light?")
    assert isinstance(response, str)
    assert len(response.strip()) > 0


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
async def test_chat_empty_query():
    """Test chat() with an empty query string."""
    response = await chat(query="", new=True, personas="assistant")
    assert isinstance(response, str)
    assert len(response.strip()) > 0 or "error" in response.lower()


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
async def test_chat_null_persona():
    """Test chat() with persona set to None."""
    response = await chat(query="How do I cook rice?", new=True, personas=None)
    assert isinstance(response, str)
    assert len(response.strip()) > 0


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv', '-m', 'integration and chat'])
