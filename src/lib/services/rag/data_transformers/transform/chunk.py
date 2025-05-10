#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides functions to transform elements' text into chunks
using the LanChain splitter functions
"""

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter
)


def transform_chunk(chunk_size, chunk_overlap, token_chunk, elements):
    """
    Transform the text of elements into chunks.

    :param chunk_size: Size of character chunks
    :param chunk_overlap: Overlap among chunks
    :param token_chunk: Size of token chunks
    :param elements: List of elements to transform.
    :return: List of transformed elements with chunks.
    """
    character_elements = _split_characters(chunk_size, chunk_overlap, elements)
    token_elements = _split_tokens(chunk_overlap, token_chunk, character_elements)
    return token_elements

def _split_characters(chunk_size, chunk_overlap, elements):
    character_elements = []
    character_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    for element in elements:
        text = element.get("text", "")
        metadata = element.get("metadata", {})
        # Split the text into chunks
        chunks = character_splitter.split_text(text)
        # Create new elements for each chunk, preserving the metadata
        for chunk in chunks:
            new_element = {
                "text": chunk,
                "metadata": metadata,
                # Include any other keys present in the original element
                **{k: v for k, v in element.items() if k not in ["text", "metadata"]}
            }
            character_elements.append(new_element)
    return character_elements

def _split_tokens(chunk_overlap, token_chunk, character_elements):
    token_elements = []
    token_splitter = SentenceTransformersTokenTextSplitter(
        chunk_overlap=chunk_overlap,
        tokens_per_chunk=token_chunk
    )
    for element in character_elements:
        text = element.get("text", "")
        metadata = element.get("metadata", {})
        # Split the text into chunks based on tokens
        chunks = token_splitter.split_text(text)
        # Create new elements for each chunk, preserving the metadata
        for chunk in chunks:
            new_element = {
                "text": chunk,
                "metadata": metadata,
                # Include any other keys present in the original element
                **{k: v for k, v in element.items() if k not in ["text", "metadata"]}
            }
            token_elements.append(new_element)
    return token_elements
