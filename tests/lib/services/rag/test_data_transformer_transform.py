#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the functions for transforming elements' text.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from src.lib.services.chat.model import ChatModel
from src.lib.services.rag.data_transformers.transform.llm import (
    transform_summary,
    transform_qa)
from src.lib.services.rag.data_transformers.transform.chunk import (
    transform_chunk)
from src.lib.services.rag.data_transformers.transform.section import (
    transform_section_by_header,
    transform_section_by_type,
    transform_section_by_toc)


@pytest.fixture
def llm_config():
    """
    Fixture for the language model configuration.
    
    Returns:
        Dict[str, Any]: A mock configuration for the language model.
    """
    return {
        "type": "LangChainChatOpenAI",
        "model_name": "gpt-3",
        "api_key": "your_api_key"
    }


@pytest.fixture
def sample_elements():
    """
    Fixture for sample elements to be transformed.
    
    Returns:
        List[Dict[str, Any]]: A list of elements with text and metadata.
    """
    return [
        {
            "text": "This is a sample text for summarization.",
            "metadata": {
                "header": "Sample Header"
            }
        },
        {
            "text": "Another text that needs to be transformed into QA pairs.",
            "metadata": {
                "header": "Another Header"
            }
        }
    ]


@patch.object(ChatModel, 'create')
def test_transform_summary(mock_create, llm_config, sample_elements):  # pylint: disable=W0621
    """
    Test the transform_summary function to ensure it returns a summary for each element.
    
    Args:
        mock_create (Mock): Mock object for the ChatModel.create method.
        llm_config (Dict[str, Any]): The mock language model configuration.
        sample_elements (List[Dict[str, Any]]): The sample elements fixture.
    """
    mock_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.content = "This is a summary."
    mock_instance.invoke.return_value = mock_result
    mock_create.return_value = mock_instance
    system_prompt = "Summarize the following text:"
    action_prompt = "Please summarize this text."
    transform_delimiters = ["**User Input:**", "```"]
    transformed_elements = transform_summary(
        llm_config,
        system_prompt,
        action_prompt,
        transform_delimiters,
        sample_elements
    )
    assert len(transformed_elements) == len(sample_elements)
    for element in transformed_elements:
        assert element['text'] == "This is a summary."
        assert 'section' in element['metadata']
    mock_instance.invoke.assert_called()


@patch.object(ChatModel, 'create')
def test_transform_qa(mock_create, llm_config, sample_elements):  # pylint: disable=W0621
    """
    Test the transform_qa function to ensure it returns QA pairs for each element.
    
    Args:
        mock_create (Mock): Mock object for the ChatModel.create method.
        llm_config (Dict[str, Any]): The mock language model configuration.
        sample_elements (List[Dict[str, Any]]): The sample elements fixture.
    """
    mock_instance = MagicMock()

    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.content = (
        "[{'question': 'What is this?', 'answer': 'This is a test.'}," 
        "{'question': 'What is that?', 'answer': 'That is a test.'}]"
    )
    mock_instance.invoke.return_value = mock_result
    mock_create.return_value = mock_instance
    system_prompt = "Generate QA pairs for the following text:"
    action_prompt = "Please generate QA pairs."
    transform_delimiters = ["**User Input:**", "```"]
    transformed_elements = transform_qa(
        llm_config,
        system_prompt,
        action_prompt,
        transform_delimiters,
        sample_elements
    )
    assert len(transformed_elements) > len(sample_elements)  # QA pairs could be more than elements
    for element in transformed_elements:
        assert 'answer' in element['metadata']
        assert 'section' in element['metadata']
    mock_instance.invoke.assert_called()


def test_transform_summary_with_invalid_config(sample_elements):  # pylint: disable=W0621
    """
    Test transform_summary with an invalid configuration to ensure it raises a RuntimeError.
    
    Args:
        sample_elements (List[Dict[str, Any]]): The sample elements fixture.
    """
    invalid_config = {"type": "InvalidModel"}
    with pytest.raises(ValueError):
        transform_summary(
            invalid_config,
            "Summarize the following text:",
            "Please summarize this text.",
            ["**User Input:**", "```"],
            sample_elements
        )


def test_transform_qa_with_invalid_config(sample_elements):  # pylint: disable=W0621
    """
    Test transform_qa with an invalid configuration to ensure it raises a RuntimeError.
    
    Args:
        sample_elements (List[Dict[str, Any]]): The sample elements fixture.
    """
    invalid_config = {"type": "InvalidModel"}
    with pytest.raises(ValueError):
        transform_qa(
            invalid_config,
            "Generate QA pairs for the following text:",
            "Please generate QA pairs.",
            ["**User Input:**", "```"],
            sample_elements
        )


@patch('src.lib.services.rag.data_transformers.transform.chunk.RecursiveCharacterTextSplitter')
@patch('src.lib.services.rag.data_transformers.transform.chunk.SentenceTransformersTokenTextSplitter')  # pylint: disable=C0301
def test_transform_chunk(mock_token_splitter, mock_char_splitter, sample_elements):  # pylint: disable=W0621
    """
    Test the transform_chunk function to ensure it splits text into character and token chunks.
    
    Args:
        mock_token_splitter (Mock): Mock object for the SentenceTransformersTokenTextSplitter.
        mock_char_splitter (Mock): Mock object for the RecursiveCharacterTextSplitter.
        sample_elements (List[Dict[str, Any]]): The sample elements fixture.
    """
    # Mock the behavior of the RecursiveCharacterTextSplitter
    mock_char_instance = MagicMock()
    mock_char_instance.split_text.return_value = [
        "This is a sample text",
        "for testing the chunking functionality."
    ]
    mock_char_splitter.return_value = mock_char_instance
    # Mock the behavior of the SentenceTransformersTokenTextSplitter
    mock_token_instance = MagicMock()
    mock_token_instance.split_text.return_value = [
        "This is a sample",
        "text for testing",
        "the chunking functionality."
    ]
    mock_token_splitter.return_value = mock_token_instance
    chunk_size = 10
    chunk_overlap = 2
    token_chunk = 5
    transformed_elements = transform_chunk(chunk_size, chunk_overlap, token_chunk, sample_elements)
    assert len(transformed_elements) == 12
    assert transformed_elements[0]['text'] == "This is a sample"
    assert transformed_elements[1]['text'] == "text for testing"
    assert transformed_elements[2]['text'] == "the chunking functionality."
    assert 'metadata' in transformed_elements[0]
    assert transformed_elements[0]['metadata']['header'] == "Sample Header"
    mock_char_instance.split_text.assert_called()
    mock_token_instance.split_text.assert_called()


@patch('src.lib.services.rag.data_transformers.transform.chunk.RecursiveCharacterTextSplitter')
@patch('src.lib.services.rag.data_transformers.transform.chunk.SentenceTransformersTokenTextSplitter')  # pylint: disable=C0301
def test_transform_chunk_preserves_metadata(mock_token_splitter, mock_char_splitter, sample_elements):  # pylint: disable=W0621, C0301
    """
    Test to ensure that metadata is preserved when text is split into chunks.
    
    Args:
        mock_token_splitter (Mock): Mock object for the SentenceTransformersTokenTextSplitter.
        mock_char_splitter (Mock): Mock object for the RecursiveCharacterTextSplitter.
        sample_elements (List[Dict[str, Any]]): The sample elements fixture.
    """
    # Mock the behavior of the RecursiveCharacterTextSplitter
    mock_char_instance = MagicMock()
    mock_char_instance.split_text.return_value = [
        "This is a sample text",
        "for testing the chunking functionality."
    ]
    mock_char_splitter.return_value = mock_char_instance
    # Mock the behavior of the SentenceTransformersTokenTextSplitter
    mock_token_instance = MagicMock()
    mock_token_instance.split_text.return_value = [
        "This is a sample",
        "text for testing",
        "the chunking functionality."
    ]
    mock_token_splitter.return_value = mock_token_instance
    chunk_size = 10
    chunk_overlap = 2
    token_chunk = 5
    transformed_elements = transform_chunk(chunk_size, chunk_overlap, token_chunk, sample_elements)
    # Ensure metadata is preserved
    for element in transformed_elements:
        assert 'metadata' in element
        assert element['metadata']['header'] in ["Sample Header", "Another Header"]
    mock_char_instance.split_text.assert_called()
    mock_token_instance.split_text.assert_called()


@pytest.fixture
def header_samples():
    """
    Fixture for sample elements to be transformed into sections.
    
    Returns:
        List[Dict[str, Any]]: A list of elements with text and metadata.
    """
    return [
        {
            "text": "Header 1",
            "metadata": {
                "type": "header",
                "header": "H1"
            }
        },
        {
            "text": "This is the first section.",
            "metadata": {
                "type": "paragraph",
                "header": None
            }
        },
        {
            "text": "Header 2",
            "metadata": {
                "type": "header",
                "header": "H2"
            }
        },
        {
            "text": "This is the second section.",
            "metadata": {
                "type": "paragraph",
                "header": None
            }
        }
    ]


def test_transform_section_by_header(header_samples):  # pylint: disable=W0621
    """
    Test the transform_section_by_header function to ensure sections are grouped under headers.
    
    Args:
        header_samples (List[Dict[str, Any]]): The header samples fixture.
    """
    transformed_elements = transform_section_by_header(header_samples)
    assert len(transformed_elements) == 2
    assert transformed_elements[0]["text"] == "Header 1\nThis is the first section."
    assert transformed_elements[1]["text"] == "Header 2\nThis is the second section."


def test_transform_section_by_type(header_samples):  # pylint: disable=W0621
    """
    Test the transform_section_by_type function to ensure sections are grouped by type.

    Args:
        header_samples (List[Dict[str, Any]]): The header samples fixture.
    """
    header_types = ["header"]
    transformed_elements = transform_section_by_type(header_types, header_samples)
    assert len(transformed_elements) == 2
    assert transformed_elements[0]["text"] == "Header 1\nThis is the first section."
    assert transformed_elements[1]["text"] == "Header 2\nThis is the second section."


def test_transform_section_by_toc():
    """
    Test the transform_section_by_toc function to ensure sections are grouped based on TOC.

    """
    toc_pattern = r'^Chapter\s\d+:\s(.+)$'
    toc_types = ["toc"]
    elements = [
        {
            "text": "Chapter 1: Introduction",
            "metadata": {
                "type": "toc",
                "header": None
            }
        },
        {
            "text": "Chapter 2: Methodology",
            "metadata": {
                "type": "toc",
                "header": None
            }
        },{
            "text": "Introduction",
            "metadata": {
                "type": "header",
                "header": None
            }
        },
        {
            "text": "This is the introduction section.",
            "metadata": {
                "type": "paragraph",
                "header": None
            }
        },
        {
            "text": "Methodology",
            "metadata": {
                "type": "header",
                "header": None
            }
        },
        {
            "text": "This is the methodology section.",
            "metadata": {
                "type": "paragraph",
                "header": None
            }
        }
    ]
    transformed_elements = transform_section_by_toc(toc_types, toc_pattern, elements)
    assert len(transformed_elements) == 2
    assert transformed_elements[0]["text"] == "Introduction\nThis is the introduction section."  # pylint: disable=C0301
    assert transformed_elements[1]["text"] == "Methodology\nThis is the methodology section."  # pylint: disable=C0301


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
