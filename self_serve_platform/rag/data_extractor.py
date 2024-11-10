#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataExtractor Module

This module defines the DataExtractor class and associated classes for 
parsing documents. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from self_serve_platform.rag.data_extractors.unstructured_for_sections import (
    UnstructuredSectionsDataExtractor)
from self_serve_platform.rag.data_extractors.pymupdf_for_sections import (
    PyMuPdfForSectionsDataExtractor)
from self_serve_platform.rag.data_extractors.pandas_read_excel import (
    PandasReadExcelExtractor)


class DataExtractor:  # pylint: disable=R0903
    """
    A section parser that uses a factory pattern to return
    the selected Data Extractor.
    """

    _extractors: Dict[str, Type] = {
        'UnstructuredForSections': UnstructuredSectionsDataExtractor,
        'PyMuPdfForSections': PyMuPdfForSectionsDataExtractor,
        'PandasReadExcel': PandasReadExcelExtractor,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return the appropriate Data Extractor based on the provided configuration.

        :param config: Configuration dictionary containing the type of extractor.
        :return: An instance of the selected data extractor.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        extractor_type = config.get('type')
        if not extractor_type:
            raise ValueError("Configuration must include 'type'.")
        extractor_class = DataExtractor._extractors.get(extractor_type)
        if not extractor_class:
            raise ValueError(f"Unsupported extractor type: {extractor_type}")
        return extractor_class(config)