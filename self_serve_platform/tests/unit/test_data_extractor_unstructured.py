#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataExtractor factory and the PyMuPdfForSectionsDataExtractor class.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate extractor types based on the given configuration, and that the parsing process 
handles files correctly, including error handling and caching.
"""

import os
from unittest.mock import patch, MagicMock, ANY
import pytest
import nltk
from self_serve_platform.rag.data_extractor import DataExtractor
from self_serve_platform.rag.data_extractors.unstructured_for_sections import (
    UnstructuredSectionsDataExtractor)


nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('maxent_ne_chunker')
nltk.download('words')


@pytest.mark.parametrize("expected_config, expected_class", [
    (
        {"type": "UnstructuredForSections"},
        UnstructuredSectionsDataExtractor
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
def unstructured_config():
    """
    Fixture to provide a mock configuration for UnstructuredSectionsDataExtractor.
    """
    return {
        "type": "UnstructuredForSections",
        "document_type": "Docx",
        "cache_elements_to_file": False,
        "extract_text": True,
        "extract_image": False,
        "header_style": "Heading",
        "header_pattern": r'(.+)$'
    }


@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.FileCache')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.Logger.get_logger')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.partition_docx')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.Document')
def test_parse_docx_success(
        mock_document,  # pylint: disable=W0613
        mock_partition_docx,
        mock_get_logger,
        mock_file_cache,
        unstructured_config):  # pylint: disable=W0621
    """
    Test the parse method to ensure it successfully parses
    a DOCX file and returns the expected result.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock the partitioning behavior
    mock_elements = [MagicMock()]
    mock_partition_docx.return_value = mock_elements
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    doc_extractor = UnstructuredSectionsDataExtractor(unstructured_config)
    result = doc_extractor.parse("sample.docx")
    assert result.status == "success"
    assert result.elements is not None
    mock_partition_docx.assert_called_once_with("sample.docx")


@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.FileCache')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.Logger.get_logger')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.partition_pdf')
def test_parse_pdf_success(
        mock_partition_pdf,
        mock_get_logger,
        mock_file_cache,
        unstructured_config):  # pylint: disable=W0621
    """
    Test the parse method to ensure it successfully parses
    a PDF file and returns the expected result.
    """
    unstructured_config["document_type"] = "Pdf"
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Mock the partitioning behavior
    mock_elements = [MagicMock()]
    mock_partition_pdf.return_value = mock_elements
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    pdf_extractor = UnstructuredSectionsDataExtractor(unstructured_config)
    result = pdf_extractor.parse("sample.pdf")
    assert result.status == "success"
    assert result.elements is not None
    mock_partition_pdf.assert_called_once_with("sample.pdf")


@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.FileCache')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.Logger.get_logger')
@patch('self_serve_platform.rag.data_extractors.unstructured_for_sections.partition_docx')
def test_parse_docx_exception_handling(
        mock_partition_docx,
        mock_get_logger,
        mock_file_cache,
        unstructured_config):  # pylint: disable=W0621
    """
    Test the parse method to ensure it handles exceptions during parsing correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    # Set up the cache mock behavior
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    # Mock an exception during document parsing
    mock_partition_docx.side_effect = Exception("Parsing error")
    doc_extractor = UnstructuredSectionsDataExtractor(unstructured_config)
    result = doc_extractor.parse("sample.docx")
    assert result.status == "failure"
    assert "An error occurred while extracting the document" in result.error_message


@pytest.fixture
def config():
    "test config"
    return {
        "type": "UnstructuredSections",
        "header_style": "Heading",
        "header_pattern": r'(.+)$',
        "exclude_header": True,
        "exclude_footer": True,
        "extract_image": True,
        "document_type": "Pdf",
        "cache_elements_to_file": False,
        "image_output_folder": "self_serve_platform/tests/unit/test_data/img"
    }

@pytest.fixture
def sample_pdf_path():
    "test path"
    return "self_serve_platform/tests/unit/test_data/sample_pdf_for_test.pdf"

@pytest.fixture
def extractor(config):  # pylint: disable=W0621
    "test extractor"
    return UnstructuredSectionsDataExtractor(config)

@pytest.fixture(autouse=True)
def clear_image_folder(config):  # pylint: disable=W0621
    """
    Clears the image output folder before each test that involves image extraction.
    """
    if os.path.exists(config["image_output_folder"]):
        for file in os.listdir(config["image_output_folder"]):
            file_path = os.path.join(config["image_output_folder"], file)
            if os.path.isfile(file_path):
                os.remove(file_path)

def test_extract_successful(extractor, sample_pdf_path):  # pylint: disable=W0621
    """
    Test if the extraction from the PDF is successful without errors.
    """
    result = extractor.parse(sample_pdf_path)
    assert result.status == "success", f"Extraction failed with error: {result.error_message}"


def test_check_extracted_elements(extractor, sample_pdf_path):  # pylint: disable=W0621
    """
    Test if the PDF elements (text, tables, images) are correctly extracted.
    """
    result = extractor.parse(sample_pdf_path)
    assert len(result.elements) > 0, "No elements were extracted from the PDF"
    assert any(elem['metadata']['type'] == "NarrativeText" for elem in result.elements), \
        "Text elements were not extracted"
    assert any("table" in elem['text'].lower() for elem in result.elements), \
        "Table elements were not extracted"
    assert any("image" in elem['metadata']['type'].lower() for elem in result.elements), \
        "Image elements were not extracted"


def test_check_no_image_extraction(sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test that images are not extracted when the extract_image flag is set to False.
    """
    config["extract_image"] = False
    extractor_no_image = UnstructuredSectionsDataExtractor(config)
    extractor_no_image.parse(sample_pdf_path)
    assert os.listdir(config["image_output_folder"]) == [], \
        "Images were extracted even when flag is False"


def test_check_image_extraction(extractor, sample_pdf_path, config):  # pylint: disable=W0621
    """
    Test if images are correctly extracted from the PDF when the extract_image flag is enabled.
    """
    extractor.parse(sample_pdf_path)
    assert os.path.exists(config["image_output_folder"]), "No images were extracted"
    extracted_images = os.listdir(config["image_output_folder"])
    assert len(extracted_images) > 0, "No image files were saved"


def test_invalid_pdf(config):  # pylint: disable=W0621
    """
    Test if the extractor handles invalid or empty PDF files gracefully, returning a failure status.
    """
    extractor = UnstructuredSectionsDataExtractor(config)  # pylint: disable=W0621
    invalid_pdf_path = "./invalid_pdf.pdf"
    with open(invalid_pdf_path, "wb") as f:
        f.write(b"")
    result = extractor.parse(invalid_pdf_path)
    assert result.status == "failure", "Extraction should fail for an invalid PDF"
    os.remove(invalid_pdf_path)


@pytest.fixture
def docx_config():
    "test config"
    return {
        "type": "UnstructuredSections",
        "header_style": "Heading",
        "header_pattern": r'(.+)$',
        "exclude_header": True,
        "exclude_footer": True,
        "extract_image": False,
        "document_type": "Docx",
        "cache_elements_to_file": False,
        "image_output_folder": "self_serve_platform/tests/unit/test_data/img"
    }

@pytest.fixture
def sample_docx_path():
    "test path"
    return "self_serve_platform/tests/unit/test_data/sample_docx_for_test.docx"

@pytest.fixture
def docx_extractor(docx_config):  # pylint: disable=W0621
    "test extractor"
    return UnstructuredSectionsDataExtractor(docx_config)


def test_extract_docx_successful(docx_extractor, sample_docx_path):  # pylint: disable=W0621
    """
    Test if the extraction from the DOCX file is successful without errors.
    """
    result = docx_extractor.parse(sample_docx_path)
    assert result.status == "success", f"Extraction failed with error: {result.error_message}"


def test_check_extracted_docx_elements(docx_extractor, sample_docx_path):  # pylint: disable=W0621
    """
    Test if the DOCX elements (text, tables, images) are correctly extracted.
    """
    result = docx_extractor.parse(sample_docx_path)
    assert len(result.elements) > 0, "No elements were extracted from the DOCX"
    assert any(elem['metadata']['type'] == "NarrativeText" for elem in result.elements), \
        "Text elements were not extracted"
    assert any("table" in elem['text'].lower() for elem in result.elements), \
        "Table elements were not extracted"


def test_check_no_image_docx_extraction(sample_docx_path, docx_config):  # pylint: disable=W0621
    """
    Test that images are not extracted when the extract_image flag is set to False.
    """
    docx_config["extract_image"] = False
    extractor_no_image = UnstructuredSectionsDataExtractor(docx_config)
    extractor_no_image.parse(sample_docx_path)
    assert os.listdir(docx_config["image_output_folder"]) == [], \
        "Images were extracted even when flag is False"


def test_exclude_header_and_footer(sample_docx_path, docx_config):  # pylint: disable=W0621
    """
    Test if headers and footers are excluded based on the configuration.
    """
    docx_config["exclude_header"] = True
    docx_config["exclude_footer"] = True
    extractor_exclude = UnstructuredSectionsDataExtractor(docx_config)
    result_exclude = extractor_exclude.parse(sample_docx_path)
    assert not any(elem['metadata']['type'] == "Header" for elem in result_exclude.elements), \
        "Headers were not excluded"
    assert not any(elem['metadata']['type'] == "Footer" for elem in result_exclude.elements), \
        "Footers were not excluded"


def test_invalid_docx(docx_config):  # pylint: disable=W0621
    """
    Test if the extractor handles invalid or empty DOCX files gracefully,
    returning a failure status.
    """
    extractor = UnstructuredSectionsDataExtractor(docx_config)  # pylint: disable=W0621
    invalid_docx_path = "./invalid_docx.docx"
    with open(invalid_docx_path, "wb") as f:
        f.write(b"")
    result = extractor.parse(invalid_docx_path)
    assert result.status == "failure", "Extraction should fail for an invalid DOCX"
    os.remove(invalid_docx_path)


@pytest.fixture
def html_config():
    "test config for HTML extraction"
    return {
        "type": "UnstructuredSections",
        "header_style": "Heading",
        "header_pattern": r'(.+)$',
        "exclude_header": True,
        "exclude_footer": True,
        "extract_image": False,
        "document_type": "Html",
        "cache_elements_to_file": False,
        "skip_start_elements": 1,
        "skip_end_elements": 1,
        "include_text_as_html": True,
        "image_output_folder": "self_serve_platform/tests/unit/test_data/img"
    }

@pytest.fixture
def sample_html_path():
    "test path for HTML"
    return "self_serve_platform/tests/unit/test_data/sample_html_for_test.html"

@pytest.fixture
def html_extractor(html_config):  # pylint: disable=W0621
    "test extractor for HTML"
    return UnstructuredSectionsDataExtractor(html_config)


def test_extract_html_successful(html_extractor, sample_html_path):  # pylint: disable=W0621
    """
    Test if the extraction from the HTML file is successful without errors.
    """
    result = html_extractor.parse(sample_html_path)
    assert result.status == "success", f"Extraction failed with error: {result.error_message}"


def test_check_extracted_html_elements(html_extractor, sample_html_path):  # pylint: disable=W0621
    """
    Test if the HTML elements (text, tables, images) are correctly extracted.
    """
    result = html_extractor.parse(sample_html_path)
    assert len(result.elements) > 0, "No elements were extracted from the HTML"
    assert any(elem['metadata']['type'] == "NarrativeText" for elem in result.elements), \
        "Text elements were not extracted"
    assert any("table" in elem['text'].lower() for elem in result.elements), \
        "Table elements were not extracted"


def test_skip_border_elements_html(html_extractor, sample_html_path):  # pylint: disable=W0621
    """
    Test if the `skip_start_elements` and `skip_end_elements` configuration skips the expected
    number of elements from the start and end of the extracted elements.
    """
    result = html_extractor.parse(sample_html_path)
    assert len(result.elements) > 0, "No elements were extracted from the HTML"
    # Assuming the HTML has more than 2 elements for this test to make sense
    assert len(result.elements) == 9, \
        f"Expected {9} elements after skipping, but got {len(result.elements)}"


def test_include_text_as_html(html_extractor, sample_html_path):  # pylint: disable=W0621
    """
    Test if the `include_text_as_html` configuration correctly includes the HTML representation
    of the text in the extracted elements when set to True.
    """
    result = html_extractor.parse(sample_html_path)
    assert len(result.elements) > 0, "No elements were extracted from the HTML"
    # Check if any element has 'text_as_html' in the metadata or if the text is returned as HTML
    assert any(
        elem['text'].startswith("<") and elem['text'].endswith(">")
        for elem in result.elements), \
        "Text elements were not extracted as HTML when `include_text_as_html` is True"


@pytest.mark.parametrize(
    "file_name, expected_partition_func_name",
    [
        ("self_serve_platform/tests/unit/test_data/sample_docx_for_test.docx", "partition_docx"),
        ("self_serve_platform/tests/unit/test_data/sample_pdf_for_test.pdf", "partition_pdf"),
        ("self_serve_platform/tests/unit/test_data/sample_html_for_test.html", "partition_html"),
        ("self_serve_platform/tests/unit/test_data/sample_pptx_for_test.pptx", "partition_pptx"),
        ("self_serve_platform/tests/unit/test_data/sample_xlsx_for_test.xlsx", "partition_xlsx"),
    ],
)
@patch("self_serve_platform.rag.data_extractors.unstructured_for_sections.FileCache")
@patch("self_serve_platform.rag.data_extractors.unstructured_for_sections.Logger.get_logger")
def test_parse_auto_document_type(
    mock_get_logger,
    mock_file_cache,
    file_name,
    expected_partition_func_name,
    unstructured_config,  # pylint: disable=W0621
):
    """
    Test that when `document_type` is set to "Auto", the correct partition function
    is called based on the file extension.
    """
    # 1. Set the doc type to "Auto".
    unstructured_config["document_type"] = "Auto"
    # 2. Patch the relevant partition functions. We can patch them all and only one will be called.
    func_name = expected_partition_func_name
    with patch(
        f"self_serve_platform.rag.data_extractors.unstructured_for_sections.{func_name}"
    ) as mock_partition_func:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        # Mock the partitioning behavior
        mock_elements = [MagicMock()]
        mock_partition_func.return_value = mock_elements
        # Set up the cache mock
        mock_file_cache_instance = mock_file_cache.return_value
        mock_file_cache_instance.is_cached.return_value = False
        # 3. Create the extractor and parse
        auto_extractor = UnstructuredSectionsDataExtractor(unstructured_config)
        result = auto_extractor.parse(file_name)
        # 4. Assertions
        assert result.status == "success"
        assert result.elements is not None
        if func_name != "partition_html":
            mock_partition_func.assert_called_once_with(ANY)


@patch("self_serve_platform.rag.data_extractors.unstructured_for_sections.FileCache")
@patch("self_serve_platform.rag.data_extractors.unstructured_for_sections.Logger.get_logger")
def test_parse_auto_unsupported_extension(
    mock_get_logger,
    mock_file_cache,
    unstructured_config  # pylint: disable=W0621
):
    """
    Test that when `document_type` is "Auto" but the file extension is unsupported,
    the extractor gracefully returns a failure status.
    """
    unstructured_config["document_type"] = "Auto"
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    mock_file_cache_instance = mock_file_cache.return_value
    mock_file_cache_instance.is_cached.return_value = False
    auto_extractor = UnstructuredSectionsDataExtractor(unstructured_config)
    # This file extension is not in your auto-detection logic.
    result = auto_extractor.parse("sample.xyz")
    assert result.status == "failure"


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
