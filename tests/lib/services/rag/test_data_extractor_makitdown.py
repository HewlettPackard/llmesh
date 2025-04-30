#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataExtractor factory and the MarkitdownForSectionsDataExtractor class.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate extractor types based on the given configuration, and that the parsing process 
handles files correctly, including error handling and caching.
"""
import os
from unittest.mock import patch, MagicMock
import pytest
from src.lib.services.rag.data_extractors.markitdown.sections import (
    MarkitdownForSectionsDataExtractor
)


@pytest.fixture
def config():
    """Fixture for the configuration of the MarkitdownForSectionsDataExtractor."""
    return {
        "type": "MarkitdownForSections",
        "cache_elements_to_file": False,
    }

@pytest.fixture
def sample_html_path():
    """Fixture for a sample HTML file path."""
    return "lib/tests/unit/test_data/sample_html_for_test.html"

@pytest.fixture
def sample_pdf_path():
    """Fixture for a sample PDF file path."""
    return "lib/tests/unit/test_data/sample_pdf_for_test.pdf"

@pytest.fixture
def sample_doc_path():
    """Fixture for a sample DOC file path."""
    return "lib/tests/unit/test_data/sample_doc_for_test.docx"

@pytest.fixture
def sample_excel_path():
    """Fixture for a sample Excel file path."""
    return "lib/tests/unit/test_data/sample_excel_for_test.xlsx"

@pytest.fixture
def extractor(config):  # pylint: disable=W0621
    """Fixture for initializing the MarkitdownForSectionsDataExtractor."""
    return MarkitdownForSectionsDataExtractor(config)


@patch('src.lib.services.rag.data_extractors.markitdown.sections.FileCache')
@patch('src.lib.services.rag.data_extractors.markitdown.sections.Logger.get_logger')
def test_parse_html_success(mock_get_logger, mock_file_cache, extractor, sample_html_path):  # pylint: disable=W0621
    """
    Test if the parsing of an HTML file is successful without errors.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mocking MarkItDown behavior
    with patch(
        'src.lib.services.rag.data_extractors.markitdown.sections.MarkItDown'
    ) as mock_markitdown:
        mock_markitdown_instance = mock_markitdown.return_value
        mock_markitdown_instance.convert.return_value.text_content = (
            "<h1>Header 1</h1><p>Some content.</p>"
        )
        result = extractor.parse(sample_html_path)
        assert result.status == "success"
        assert len(result.elements) == 1  # Single segment expected
        assert result.elements[0]["text"].strip() == '<h1>Header 1</h1><p>Some content.</p>'


@patch('src.lib.services.rag.data_extractors.markitdown.sections.FileCache')
@patch('src.lib.services.rag.data_extractors.markitdown.sections.Logger.get_logger')
def test_parse_pdf_success(mock_get_logger, mock_file_cache, extractor, sample_pdf_path):  # pylint: disable=W0621
    """
    Test if the parsing of a PDF file is successful without errors.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mocking MarkItDown behavior
    with patch(
        'src.lib.services.rag.data_extractors.markitdown.sections.MarkItDown'
    ) as mock_markitdown:
        mock_markitdown_instance = mock_markitdown.return_value
        mock_markitdown_instance.convert.return_value.text_content = (
            "# PDF Header\nThis is content from the PDF."
        )
        result = extractor.parse(sample_pdf_path)
        assert result.status == "success"
        assert len(result.elements) == 1  # Header and content
        assert result.elements[0]["metadata"]["header"] == "# PDF Header"
        assert result.elements[0]["text"].strip() == "This is content from the PDF."


@patch('src.lib.services.rag.data_extractors.markitdown.sections.FileCache')
@patch('src.lib.services.rag.data_extractors.markitdown.sections.Logger.get_logger')
def test_parse_doc_success(mock_get_logger, mock_file_cache, extractor, sample_doc_path):  # pylint: disable=W0621
    """
    Test if the parsing of a DOC file is successful without errors.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mocking MarkItDown behavior
    with patch(
        'src.lib.services.rag.data_extractors.markitdown.sections.MarkItDown'
    ) as mock_markitdown:
        mock_markitdown_instance = mock_markitdown.return_value
        mock_markitdown_instance.convert.return_value.text_content = (
            "# DOC Header\nThis is content from the DOC."
        )
        result = extractor.parse(sample_doc_path)
        assert result.status == "success"
        assert len(result.elements) == 1  # Header and content
        assert result.elements[0]["metadata"]["header"] == "# DOC Header"
        assert result.elements[0]["text"].strip() == "This is content from the DOC."


@patch('src.lib.services.rag.data_extractors.markitdown.sections.FileCache')
@patch('src.lib.services.rag.data_extractors.markitdown.sections.Logger.get_logger')
def test_parse_excel_success(mock_get_logger, mock_file_cache, extractor, sample_excel_path):  # pylint: disable=W0621
    """
    Test if the parsing of an Excel file is successful without errors.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mocking MarkItDown behavior
    with patch(
        'src.lib.services.rag.data_extractors.markitdown.sections.MarkItDown'
    ) as mock_markitdown:
        mock_markitdown_instance = mock_markitdown.return_value
        mock_markitdown_instance.convert.return_value.text_content = (
            "<!-- Sheet1 -->\n# Excel Header\nCell content"
        )
        result = extractor.parse(sample_excel_path)
        assert result.status == "success"
        assert len(result.elements) == 1  # Header and content
        assert result.elements[0]["metadata"]["header"] == "# Excel Header"
        assert result.elements[0]["text"].strip() == "Cell content"

if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
