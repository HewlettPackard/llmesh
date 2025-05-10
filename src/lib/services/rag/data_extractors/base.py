#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Data Extractor

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field


class BaseDataExtractor(abc.ABC):  # pylint: disable=R0903
    """
    Abstract base class for data extractors.
    """

    class Config(BaseModel):
        """
        Configuration for the Data Extractor class.
        """
        type: str = Field(
            ...,
            description="Type of the extractor deployment."
        )
        document_type: str = Field(
            "Auto",
            description="Type of document."
        )
        cache_elements_to_file: Optional[bool] = Field(
            False,
            description="Save the parsed elements into a file."
        )
        extract_text: Optional[bool] = Field(
            True,
            description="Extract texts."
        )
        exclude_header: Optional[bool] = Field(
            True,
            description="Don't consider header elements."
        )
        exclude_footer: Optional[bool] = Field(
            True,
            description="Don't consider footer elements."
        )
        extract_image: Optional[bool] = Field(
            True,
            description="Extract images."
        )
        image_output_folder: Optional[str] = Field(
            ".",
            description="Folder where to store the images."
        )

    class Result(BaseModel):
        """
        Result of the data extraction process.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        elements: Optional[List[Dict[str, Any]]] = Field(
            None,
            description="Extracted document elements and their data and metadata."
        )

    @abc.abstractmethod
    def parse(self, file_path: str) -> 'BaseDataExtractor.Result':
        """
        Abstract method to parse the document.

        :param file_path: Path to the document to be parsed.
        :return: Result object containing the parsed elements and status.
        """
