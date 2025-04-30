#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unstructured Sections Data Extractor

This module allows:
- Extraction of docx, pdf or html documents using the Unstructured library
- All elements to be extracted as vanilla unstructured docx or pdf with layout parsing
- Extraction of all sections using headers or table of contents to find them
"""

import re
from typing import Optional
from types import MappingProxyType
from bs4 import BeautifulSoup
from docx import Document
from unstructured.partition.docx import partition_docx
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.xlsx import partition_xlsx
from unstructured.partition.html import partition_html
from pydantic import Field
from src.lib.services.rag.data_extractors.base import BaseDataExtractor
from src.lib.core.file_cache import FileCache
from src.lib.core.log import Logger


logger = Logger().get_logger()


class UnstructuredSectionsDataExtractor(BaseDataExtractor):  # pylint: disable=R0903
    """
    Strategy for managing data extraction from documents.
    """

    class Config(BaseDataExtractor.Config):
        """
        Configuration for the Data Extractor class
        """
        header_style: Optional[str] = Field(
            "Heading",
            description="Style of the header paragraph"
        )
        header_pattern: Optional[str] = Field(
            r'(.+)$',
            description="Pattern to match headers"
        )
        skip_start_elements: Optional[int] = Field(
            0,
            description="Number of initial elements to skip"
        )
        skip_end_elements: Optional[int] = Field(
            0,
            description="Number of end elements to skip"
        )
        include_text_as_html: Optional[bool] = Field(
            False,
            description="Keep text or replace HTML when available (e.g. table)"
        )

    def __init__(self, config):
        self.config = UnstructuredSectionsDataExtractor.Config(**config)
        self.result = UnstructuredSectionsDataExtractor.Result()
        self.file_cache = FileCache({"cache_to_file": self.config.cache_elements_to_file})

    def parse(self, file_path: str):
        """
        Parse a document file.

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
                self.result.elements = self._partition_document(file_path)
                logger.debug("Saving elements to cache.")
                self.file_cache.save(file_path, self.result.elements)
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while extracting the document: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _partition_document(self, file_path: str):
        if self.config.extract_text is False:
            logger.warning("Not possible parsing only images with unstructured")
        document_type = self._get_document_type(file_path)
        if document_type == "Docx":
            logger.debug("Partitioning Docx document.")
            elements = partition_docx(file_path)
            if self.config.extract_image:
                logger.warning("Image extraction is not implemented for Docx files.")
        elif document_type == "Pdf":
            logger.debug("Partitioning Pdf document.")
            kwargs = self._get_partition_pdf_kwargs()
            elements = partition_pdf(file_path, **kwargs)
        elif document_type == "Html":
            logger.debug("Partitioning Html document.")
            html_content = self._get_html_content(file_path)
            elements = partition_html(text=html_content)
        elif document_type == "Pptx":
            logger.debug("Partitioning Pptx document.")
            elements = partition_pptx(file_path)
            if self.config.extract_image:
                logger.warning("Image extraction is not implemented for Pptx files.")
        elif document_type == "Xlsx":
            logger.debug("Partitioning Xlsx document.")
            elements = partition_xlsx(file_path)
            if self.config.extract_image:
                logger.warning("Image extraction is not implemented for Xlsx files.")
        else:
            logger.error("Unsupported document type.")
            elements = None
        self._log_element_distribution(elements)
        elements = self._skip_border_elements(elements)
        return self._create_element_list(elements, file_path)

    def _get_document_type(self, file_path: str):
        if self.config.document_type == "Auto":
            logger.debug("Auto-detecting document type based on file extension.")
            file_extension = file_path.split('.')[-1].lower()
            if file_extension == "docx":
                return "Docx"
            if file_extension == "pdf":
                return "Pdf"
            if file_extension in {"html", "htm"}:
                return "Html"
            if file_extension == "pptx":
                return "Pptx"
            if file_extension == "xlsx":
                return "Xlsx"
            logger.error("Unsupported file extension for auto-detection.")
            return "Unsupported"
        return self.config.document_type

    def _get_partition_pdf_kwargs(self):
        kwargs = {}
        if self.config.extract_image:
            logger.debug("Partitioning with image extraction.")
            kwargs.update({
                'extract_images_in_pdf': self.config.extract_image,
                'strategy': "hi_res",
                'extract_image_block_output_dir': self.config.image_output_folder
            })
        return kwargs

    def _get_html_content(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return html_content

    def _log_element_distribution(self, elements):
        type_counts = {}
        for element in elements:
            element_type = type(element).__name__
            type_counts[element_type] = type_counts.get(element_type, 0) + 1
        logger.debug("Distribution of element types:")
        for element_type, count in type_counts.items():
            logger.debug(f"{element_type}: {count}")

    def _skip_border_elements(self, elements):
        if elements is None:
            return None
        if self.config.skip_start_elements == 0 and self.config.skip_end_elements == 0:
            return elements
        elif self.config.skip_start_elements == 0:
            return elements[:-self.config.skip_end_elements]  # pylint: disable=E1130
        elif self.config.skip_end_elements == 0:
            return elements[self.config.skip_start_elements:]
        else:
            return elements[self.config.skip_start_elements:-self.config.skip_end_elements]  # pylint: disable=E1130

    def _create_element_list(self, elements, file_path: str):
        logger.info("Parsing all elements.")
        elements_list = []
        header_elements = self._find_and_clean_header_elements(file_path)
        for element in elements:
            element_metadata = self._calculate_metadata(element, header_elements)
            self._process_and_append_element(elements_list, element, element_metadata)
        return elements_list

    def _find_and_clean_header_elements(self, file_path: str):
        header_elements = []
        if self.config.document_type == "Docx":
            doc = Document(file_path)
            header_elements = [
                self._clean_header(paragraph.text)
                for paragraph in doc.paragraphs
                if paragraph.style.name.startswith(self.config.header_style)
            ]
        elif self.config.document_type == "Html":
            html_content = self._get_html_content(file_path)
            soup = BeautifulSoup(html_content, 'lxml')
            h_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            header_elements = [tag.get_text() for tag in h_tags]
        else:
            logger.warning("Header detection method available only for docx")
        return header_elements

    def _clean_header(self, header: str):
        return ' '.join(header.replace('\t', ' ').split())

    def _calculate_metadata(self, element, header_elements):
        metadata = self._convert_unstructured_metadata(element)
        metadata['type'] = type(element).__name__
        metadata["id"] = element._element_id  # pylint: disable=W0212
        metadata["header"] = self._match_header(element, header_elements)
        return metadata

    def _convert_unstructured_metadata(self, element):
        metadata = {}
        if hasattr(element, 'metadata'):
            metadata = {
                attr: getattr(element.metadata, attr)
                for attr in dir(element.metadata)
                if not callable(getattr(element.metadata, attr)) and
                not attr.startswith("__") and
                not isinstance(getattr(element.metadata, attr),
                    (frozenset, MappingProxyType))
            }
        return metadata

    def _match_header(self, element, header_elements):
        cleaned_text = self._clean_header(element.text)
        for header in header_elements:
            match = re.search(self.config.header_pattern, cleaned_text)
            if match and match.group(1) == header:
                return cleaned_text
        return None

    def _process_and_append_element(self, elements_list, element, element_metadata):
        if not self._should_exclude_element(element_metadata):
            elements_list.append({
                "text": self._get_element_text(element, element_metadata),
                "metadata": element_metadata
            })

    def _should_exclude_element(self, element_metadata):
        return (
            (self.config.exclude_header and element_metadata["type"] == "Header") or
            (self.config.exclude_footer and element_metadata["type"] == "Footer")
        )

    def _get_element_text(self, element, element_metadata):
        if self.config.include_text_as_html:
            return element_metadata.get('text_as_html', element.text)
        return element.text
