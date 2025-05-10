#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the PandasReadExcelExtractor class.
The tests ensure that the extractor correctly initializes, parses an Excel file, 
and processes the data by transforming it into text and metadata as expected.
"""

import os
import pytest
from src.lib.services.rag.data_extractor import DataExtractor
from src.lib.services.rag.data_extractors.pandas.read_excel import (
    PandasReadExcelExtractor)


@pytest.mark.parametrize("expected_config, expected_class", [
    (
        {
            "type": "PandasReadExcel",
            "text_columns": ["ColumnA"]
        },
        PandasReadExcelExtractor
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
def config():
    """
    Test config for the PandasReadExcelExtractor.
    """
    return {
        "type": "PandasReadExcel",
        "text_columns": ["Requirement", "Details"],
        "filter_metadata_columns": ["ExcludeColumn"],
        "sheet_name": 0,
        "cache_elements_to_file": False
    }


@pytest.fixture
def sample_excel_file():
    """
    Path to the real sample Excel file.
    """
    return "tests/lib/services/rag/test_data/sample_excel_for_test.xlsx"


@pytest.fixture
def extractor(config):  # pylint: disable=W0621
    """
    Test extractor fixture.
    """
    return PandasReadExcelExtractor(config)


def test_extract_successful(extractor, sample_excel_file):  # pylint: disable=W0621
    """
    Test if the extraction from the Excel file is successful without errors.
    """
    result = extractor.parse(sample_excel_file)
    assert result.status == "success", f"Extraction failed with error: {result.error_message}"


def test_check_extracted_elements(extractor, sample_excel_file):  # pylint: disable=W0621
    """
    Test if the Excel elements (text, metadata) are correctly extracted.
    """
    result = extractor.parse(sample_excel_file)
    assert len(result.elements) > 0, "No elements were extracted from the Excel"
    # Check if text is correctly formed from the text columns
    for elem in result.elements:
        assert "Req" in elem['text'], "Requirement column was not included in text"
        assert "Detail" in elem['text'], "Details column was not included in text"
    # Check if metadata is excluding the right columns
    for elem in result.elements:
        assert "exclude_column" not in elem['metadata'], "ExcludeColumn should not be in metadata"
        assert "othercolumn" in elem['metadata'], "OtherColumn should be in metadata"


def test_exclude_columns_from_metadata(extractor, sample_excel_file):  # pylint: disable=W0621
    """
    Test that columns specified in filter_metadata_columns are excluded from the metadata.
    """
    result = extractor.parse(sample_excel_file)
    for elem in result.elements:
        assert "exclude_column" not in elem['metadata'], \
            "Excluded columns were not removed from metadata"
        assert "othercolumn" in elem['metadata'], \
            "OtherColumn should not have been excluded"


def test_invalid_excel_file(extractor):  # pylint: disable=W0621
    """
    Test how the extractor handles an invalid or empty Excel file.
    """
    invalid_excel_path = "./invalid_excel.xlsx"
    with open(invalid_excel_path, "wb") as f:
        f.write(b"")
    result = extractor.parse(invalid_excel_path)
    assert result.status == "failure", "Extraction should fail for an invalid Excel file"
    os.remove(invalid_excel_path)



if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
