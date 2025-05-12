#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pandas Excel Data Extractor

This module allows:
- Extraction of excel documents using the Pandas library
- All elements to be extracted as dataframe
- Converted in json text and metadata with the columns specified in the config
"""

from typing import Optional, Union, List
import pandas as pd
from pydantic import Field
from src.lib.services.rag.data_extractors.base import BaseDataExtractor
from src.lib.core.file_cache import FileCache
from src.lib.core.log import Logger


logger = Logger().get_logger()


class PandasReadExcelExtractor(BaseDataExtractor):  # pylint: disable=R0903
    """
    Strategy for managing data extraction from documents.
    """

    class Config(BaseDataExtractor.Config):
        """
        Configuration for the Data Extractor class
        """
        text_columns: List[str] = Field(
            ...,
            description="List of columns to concatenate and use as the text for each row"
        )
        filter_metadata_columns: Optional[List[str]] = Field(
            default=[],
            description="List of columns to exclude from the metadata for each row"
        )
        sheet_name: Optional[Union[str, int]]= Field(
            0,
            description="Name of the Excel sheet to parser"
        )

    def __init__(self, config):
        self.config = PandasReadExcelExtractor.Config(**config)
        self.result = PandasReadExcelExtractor.Result()
        self.file_cache = FileCache({"cache_to_file": self.config.cache_elements_to_file})

    def parse(self, file_path: str):
        """
        Parse an excel file.

        :param file_path: Path to the document file
        :return: Result object containing the extracted elements
        """
        try:
            self.result.status = "success"
            if self.file_cache.is_cached(file_path):
                logger.debug("Loading elements from cache.")
                self.result.elements = self.file_cache.load(file_path)
            else:
                logger.debug("Parsing document.")
                self.result.elements = self._partition_excel(file_path)
                logger.debug("Saving elements to cache.")
                self.file_cache.save(file_path, self.result.elements)
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while extracting the document: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _partition_excel(self, file_path):
        dataframe = pd.read_excel(file_path, sheet_name=self.config.sheet_name)
        elements = self._transform_to_elements(dataframe)
        return elements

    def _transform_to_elements(self, df):
        # List to hold the transformed data
        elements = []
        # Determine the columns to be excluded from metadata based on config
        exclude_columns = set(self.config.text_columns + self.config.filter_metadata_columns)
        # Iterate over each row in the DataFrame
        for _, row in df.iterrows():
            # Concatenate text from the columns specified in self.config.text_columns
            text_parts = [f"{str(row[col])}" for col in self.config.text_columns]
            concatenated_text = "\n".join(text_parts)
            # Create metadata dictionary by including only columns that are not excluded
            metadata = {
                col.lower(): str(row[col]) for col in df.columns if col not in exclude_columns
            }
            # Create the JSON object for this row
            json_object = {
                'text': concatenated_text,
                'metadata': metadata
            }
            # Append the object to the list
            elements.append(json_object)
        return elements
