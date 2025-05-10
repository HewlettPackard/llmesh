#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Markitdown for Sections Data Extractor

This module allows:
- Extracting data from a different typoes of documents using the Markitdown library
- Slitting markdown in elements
"""

import re
from markitdown import MarkItDown
from src.lib.services.rag.data_extractors.base import BaseDataExtractor
from src.lib.core.file_cache import FileCache
from src.lib.core.log import Logger


logger = Logger().get_logger()


class MarkitdownForSectionsDataExtractor(BaseDataExtractor):  # pylint: disable=R0903
    """
    Strategy for managing data extraction from document sections
    """

    def __init__(self, config):
        self.config = MarkitdownForSectionsDataExtractor.Config(**config)
        self.result = MarkitdownForSectionsDataExtractor.Result()
        self.file_cache = FileCache({"cache_to_file": self.config.cache_elements_to_file})
        if self.config.document_type != "Auto":
            logger.warning("Document type is not 'Auto'. Handling it as 'Auto'.")

    def parse(self, file_path: str) -> 'BaseDataExtractor.Result':
        """
        Parse a file.

        :param file_path: Path to the file
        :return: Result object containing the extracted elements
        """
        try:
            self.result.status = "success"
            if self.file_cache.is_cached(file_path):
                logger.debug("Load elements from file.")
                self.result.elements = self.file_cache.load(file_path)
            else:
                logger.debug("Parse document.")
                self.result.elements = self._extract_elements(file_path)
                logger.debug("Save elements to file.")
                self.file_cache.save(file_path, self.result.elements)
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while extracting the document: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _extract_elements(self, file_path: str):
        md = MarkItDown()
        result = md.convert(file_path)
        elements = self._split_markdown(result.text_content, file_path)
        return elements

    def _split_markdown(self, content, file_name):
        # Regular expression to match headers and annotations
        split_pattern = r"^(#.*|<!--.*?-->)"
        segments = []
        current_segment = self._init_segment(file_name)
        for line in content.splitlines():
            match = re.match(split_pattern, line)
            if match:
                # Save the current segment if it has text
                if current_segment["text"].strip():
                    segments.append(current_segment)
                    current_segment = self._init_segment(file_name)
                # Determine if the match is an annotation or a header
                matched_line = match.group(0)
                if matched_line.startswith("<!--"):
                    current_segment["metadata"]["annotation"] = matched_line
                else:
                    current_segment["metadata"]["header"] = matched_line
            else:
                # Append line to the current segment's text
                current_segment["text"] += line + "\n"
        # Append the last segment if it has content
        if current_segment["text"].strip():
            segments.append(current_segment)
        return segments

    def _init_segment(self, file_name):
        return {
            "text": "",
            "metadata": {
                "annotation": None,
                "header": None,
                "file_name": file_name
            }
        }
