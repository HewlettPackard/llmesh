#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataExtractor factory and the PyMuPdfForSectionsDataExtractor class.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate extractor types based on the given configuration, and that the parsing process 
handles files correctly, including error handling and caching.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from libs.services.rag.data_extractor import DataExtractor
from libs.services.rag.data_extractors.pymupdf.sections import (
    PyMuPdfForSectionsDataExtractor)


@pytest.mark.parametrize("expected_config, expected_class", [
    (
        {"type": "PyMuPdfForSections"},
        PyMuPdfForSectionsDataExtractor
    )
])
def test_create(expected_config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    extractor_instance = DataExtractor.create(expected_config)
    assert isinstance(extractor_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError, match="Unsupported extractor type: InvalidType"):
        DataExtractor.create({"type": "InvalidType"})


@pytest.fixture
def pymupdf_config():
    """
    Fixture to provide a mock configuration for PyMuPdfForSectionsDataExtractor.
    """
    return {
        "type": "PyMuPdfForSections",
        "document_type": "Pdf",
        "cache_elements_to_file": False,
        "extract_text": True,
        "extract_image": False,
        "image_output_folder": ".",
        "title_size_threshold": 12,
        "convert_table_to_html": True
    }


@patch('libs.services.rag.data_extractors.pymupdf.sections.FileCache')
@patch('libs.services.rag.data_extractors.pymupdf.sections.Logger.get_logger')
@patch('fitz.open')
def test_parse_success(mock_fitz_open, mock_get_logger, mock_file_cache, pymupdf_config):  # pylint: disable=W0621
    """
    Test the parse method to ensure it successfully parses a PDF file
    and returns the expected result.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock the PDF document behavior
    mock_pdf_document = MagicMock()
    mock_fitz_open.return_value = mock_pdf_document
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mock extracted elements to simulate parsing
    mock_extracted_elements = [{"text": "Sample text", "metadata": {"type": "text"}}]
    with patch.object(
        PyMuPdfForSectionsDataExtractor,
        '_extract_elements',
        return_value=mock_extracted_elements):
        pdf_extractor = PyMuPdfForSectionsDataExtractor(pymupdf_config)
        result = pdf_extractor.parse("sample.pdf")
    assert result.status == "success"
    assert result.elements == mock_extracted_elements


@patch('libs.services.rag.data_extractors.pymupdf.sections.FileCache')
@patch('libs.services.rag.data_extractors.pymupdf.sections.Logger.get_logger')
@patch('os.path.exists', return_value=False)
def test_parse_file_not_found(mock_exists, mock_get_logger, mock_file_cache, pymupdf_config):  # pylint: disable=W0621
    """
    Test the parse method to ensure it handles a file not found scenario correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Ensure the cache indicates no cached file is available
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # No need to patch fitz.open since it should not be called if the file does not exist
    pdf_extractor = PyMuPdfForSectionsDataExtractor(pymupdf_config)
    result = pdf_extractor.parse("non_existent_file.pdf")
    assert result.status == "failure"
    assert "no such file" in result.error_message
    mock_file_cache_instance.is_cached.assert_called_once_with("non_existent_file.pdf")
    mock_file_cache_instance.load.assert_not_called()  # Ensure load is not called
    mock_exists.assert_called_once_with("non_existent_file.pdf")


@patch('libs.services.rag.data_extractors.pymupdf.sections.FileCache')
@patch('libs.services.rag.data_extractors.pymupdf.sections.Logger.get_logger')
@patch('fitz.open')
def test_parse_with_cache(mock_fitz_open, mock_get_logger, mock_file_cache, pymupdf_config):  # pylint: disable=W0621, W0613
    """
    Test the parse method to ensure it uses cached data if available.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = True
    mock_cached_elements = [{"text": "Cached text", "metadata": {"type": "text"}}]
    mock_file_cache_instance.load.return_value = mock_cached_elements
    pdf_extractor = PyMuPdfForSectionsDataExtractor(pymupdf_config)
    result = pdf_extractor.parse("cached_file.pdf")
    assert result.status == "success"
    assert result.elements == mock_cached_elements
    mock_file_cache_instance.load.assert_called_once_with("cached_file.pdf")


@patch('libs.services.rag.data_extractors.pymupdf.sections.FileCache')
@patch('libs.services.rag.data_extractors.pymupdf.sections.Logger.get_logger')
@patch('fitz.open')
def test_parse_exception_handling(mock_fitz_open, mock_get_logger, mock_file_cache, pymupdf_config):  # pylint: disable=W0621, W0613
    """
    Test the parse method to ensure it handles exceptions during parsing correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Ensure the cache indicates no cached file is available
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mock an exception during file parsing
    with patch.object(
        PyMuPdfForSectionsDataExtractor,
        '_extract_elements',
        side_effect=Exception("Parsing error")):
        pdf_extractor = PyMuPdfForSectionsDataExtractor(pymupdf_config)
        result = pdf_extractor.parse("sample.pdf")
    assert result.status == "failure"
    assert "An error occurred while extracting the document" in result.error_message

@pytest.fixture
def config():
    "test config"
    return {
        "type": "PyMuPdfForSections",
        "title_size_threshold": 12,
        "convert_table_to_html": True,
        "table_column_threshold": 20,
        "skip_header_lines": 0,
        "skip_footer_lines": 0,
        "skip_header_images": 0,
        "skip_footer_images": 0,
        "extract_text": True,
        "extract_image": True,
        "document_type": "Pdf",
        "cache_elements_to_file": False,
        "image_output_folder": "libs/services/rag/tests/test_data/img"
    }

@pytest.fixture
def sample_pdf_path():
    "test path"
    return "libs/services/rag/tests/test_data/sample_pdf_for_test.pdf"

@pytest.fixture
def extractor(config):  # pylint: disable=W0621
    "test extractor"
    return PyMuPdfForSectionsDataExtractor(config)

@pytest.fixture(autouse=True)
def clear_image_folder(config):  # pylint: disable=W0621
    """
    Clears the image output folder before each test that involves image extraction.
    """
    if os.path.exists(config["image_output_folder"]):
        for file in os.listdir(config["image_output_folder"]):
            if file == ".gitkeep":
                continue  # Skip deleting the .gitkeep file
            file_path = os.path.join(config["image_output_folder"], file)
            if os.path.isfile(file_path):
                os.remove(file_path)

def test_extract_successful(extractor, sample_pdf_path):  # pylint: disable=W0621
    """
    Test if the extraction from the PDF is successful without errors.
    """
    result = extractor.parse(sample_pdf_path)
    assert result.status == "success", f"Extraction failed with error: {result.error_message}"


def test_check_titles(extractor, sample_pdf_path):  # pylint: disable=W0621
    """
    Test if titles are correctly identified in the PDF based on font size.
    """
    result = extractor.parse(sample_pdf_path)
    assert any(elem['metadata']['type'] == "header" for elem in result.elements), \
        "No headers were extracted"


def test_check_table_conversion_to_html(extractor, sample_pdf_path):  # pylint: disable=W0621
    """
    Test if tables in the PDF are correctly identified and converted to HTML.
    """
    result = extractor.parse(sample_pdf_path)
    assert any("<table>" in elem['text'] for elem in result.elements), \
        "No tables were detected or converted to HTML"


def test_check_no_table_conversion(sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test that tables are not converted to HTML when the conversion flag is set to False.
    """
    config["convert_table_to_html"] = False
    extractor_no_html = PyMuPdfForSectionsDataExtractor(config)
    result_no_html = extractor_no_html.parse(sample_pdf_path)
    assert not any("<table>" in elem['text'] for elem in result_no_html.elements), \
        "Table was converted to HTML even when flag is False"


def test_skip_first_lines(sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test if the first few lines of text are skipped when the skip_header_lines setting is enabled.
    """
    extractor_default = PyMuPdfForSectionsDataExtractor(config)
    result_default = extractor_default.parse(sample_pdf_path)
    config["skip_header_lines"] = 2
    extractor_skip_header = PyMuPdfForSectionsDataExtractor(config)
    result_skip_header = extractor_skip_header.parse(sample_pdf_path)
    assert len(result_skip_header.elements) < len(result_default.elements), \
        "Header lines were not skipped"


def test_skip_last_lines(sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test if the last few lines of text are skipped when the skip_footer_lines setting is enabled.
    """
    extractor_default = PyMuPdfForSectionsDataExtractor(config)
    result_default = extractor_default.parse(sample_pdf_path)
    config["skip_footer_lines"] = 2
    extractor_skip_footer = PyMuPdfForSectionsDataExtractor(config)
    result_skip_footer = extractor_skip_footer.parse(sample_pdf_path)
    assert len(result_skip_footer.elements) < len(result_default.elements), \
        "Footer lines were not skipped"


def test_check_image_extraction(sample_pdf_path, extractor, config):  # pylint: disable=W0621
    """
    Test if images are correctly extracted from the PDF when the extract_image flag is enabled.
    """
    extractor.parse(sample_pdf_path)
    assert os.path.exists(config["image_output_folder"]), "No images were extracted"
    extracted_images = os.listdir(config["image_output_folder"])
    assert len(extracted_images) > 0, "No image files were saved"


def test_check_no_image_extraction(sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test that images are not extracted when the extract_image flag is set to False.
    """
    config["extract_image"] = False
    extractor_no_image = PyMuPdfForSectionsDataExtractor(config)
    extractor_no_image.parse(sample_pdf_path)
    assert os.listdir(config["image_output_folder"]) == [".gitkeep",], \
        "Images were extracted even when flag is False"


def test_skip_images(sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test if the first images are skipped when the skip_header_images setting is enabled.
    """
    extractor_default = PyMuPdfForSectionsDataExtractor(config)
    result_default = extractor_default.parse(sample_pdf_path)
    config["skip_header_images"] = 1
    extractor_skip_image = PyMuPdfForSectionsDataExtractor(config)
    extractor_skip_image.parse(sample_pdf_path)
    remaining_images = os.listdir(config["image_output_folder"])
    assert len(remaining_images) < len(result_default.elements), "Header images were not skipped"


def test_invalid_pdf(config):  # pylint: disable=W0621
    """
    Test if the extractor handles invalid or empty PDF files gracefully, returning a failure status.
    """
    extractor_invalid = PyMuPdfForSectionsDataExtractor(config)
    invalid_pdf_path = "./invalid_pdf.pdf"
    with open(invalid_pdf_path, "wb") as f:
        f.write(b"")
    result = extractor_invalid.parse(invalid_pdf_path)
    assert result.status == "failure", "Extraction should fail for an invalid PDF"
    os.remove(invalid_pdf_path)


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
