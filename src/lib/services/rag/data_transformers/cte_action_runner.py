#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unstructured for docx Data Transformer

This module allow 
- to clean data text with several methods
- to trasform data text using LLM
- to enrich metadata 
"""

from functools import partial
from typing import List, Optional, Dict, Any
from pydantic import Field
from src.lib.services.rag.data_transformers.base import BaseDataTransformer
from src.lib.services.rag.data_transformers.clean import regex
from src.lib.services.rag.data_transformers.transform import llm, section, chunk
from src.lib.services.rag.data_transformers.enrich import metadata
from src.lib.core.log import Logger


logger = Logger().get_logger()


class CteActionRunnerDataTransformer(BaseDataTransformer):  # pylint: disable=R0903
    """
    Strategy for managing data transformer
    """

    class Config(BaseDataTransformer.Config):
        """
        Arguments of the Data Transformer class
        """
        clean: Optional["CteActionRunnerDataTransformer.ConfigClean"] = Field(
            None,
            description="Configuration fields of the clean operation"
        )
        transform: Optional["CteActionRunnerDataTransformer.ConfigTransform"] = Field(
            None,
            description="Configuration fields of the transform operation"
        )

    class ConfigClean(BaseDataTransformer.ConfigClean):
        """
        Configuration for the Clean class.
        """
        headers_to_remove: Optional[List[str]] = Field(
            None,
            description="A list of headers to remove"
        )
        headers_to_keep: Optional[List[str]] = Field(
            None,
            description="A list of headers to keep"
        )
        min_section_length: Optional[int] = Field(
            100,
            description="Minimum number of characters for a section"
        )

    class ConfigTransform(BaseDataTransformer.ConfigTransform):
        """
        Configuration for the Tranform class.
        """
        llm_config: Optional[Dict[str, Any]] = Field(
            None,
            description="Configuration settings for the LLM"
        )
        system_prompt: Optional[str] = Field(
            "",
            description="Prompt to provide context for the LLM"
        )
        action_prompt: Optional[str] = Field(
            "",
            description="Prompt to provide context for the LLM"
        )
        transform_delimeters: Optional[List[str]] = Field(
            ['```', '```json'],
            description="List of delimeters of LLM transformation"
        )
        header_types: Optional[List[str]] = Field(
            ['Title', 'Header'],
            description='List of element types to consider for TOC extraction'
        )
        toc_types: Optional[List[str]] = Field(
            ['Title', 'Header', 'Text', 'NarrativeText'],
            description='List of element types to consider for TOC extraction'
        )
        toc_pattern: Optional[str] = Field(
            r'(.+?)\t(\d+)\s*$',
            description="Pattern to match ToC entries"
        )
        chunk_size: Optional[int] = Field(
            1000,
            description="Number of char processed per chunk."
        )
        chunk_overlap: Optional[int] = Field(
            0,
            description="Number of char overlapping between chunks."
        )
        token_chunk: Optional[int] = Field(
            256,
            description="Number of tokens per chunk for processing."
        )

    def __init__(self, config):
        self.config = CteActionRunnerDataTransformer.Config(**config)
        self.result = CteActionRunnerDataTransformer.Result()
        # Initialize the action_map with checks for None
        self.action_map = self._init_actions()

    # pylint: disable=E1101
    def _init_actions(self):
        action_map ={}
        self._init_clean_actions(action_map)
        self._init_transform_actions(action_map)
        self._init_enrich_actions(action_map)
        return action_map

    def _init_clean_actions(self, action_map):
        if not self.config.clean:
            self.config.clean = CteActionRunnerDataTransformer.ConfigClean(**{})
        action_map.update({
            'RemoveMultipleSpaces': regex.remove_multiple_spaces,
            'ReplaceTabsWithSpaces': partial(
                regex.replace_tabs_with_spaces,
                self.config.clean.fields  # pylint: disable=E1101
            ),
            'RemoveTitleElementsOnly': regex.remove_title_elements_only,
            'RemoveSectionsByHeader': partial(
                regex.remove_sections_by_header,
                self.config.clean.headers_to_remove
            ),
            'KeepSectionsByHeader': partial(
                regex.keep_sections_by_header,
                self.config.clean.headers_to_keep
            ),
            'RemoveShortSections': partial(
                regex.remove_short_sections,
                self.config.clean.min_section_length
            )
        })

    def _init_transform_actions(self, action_map):
        if not self.config.transform:
            self.config.transform = CteActionRunnerDataTransformer.ConfigTransform(**{})
        action_map.update({
            "TransformInSummary": partial(
                llm.transform_summary,
                self.config.transform.llm_config,
                self.config.transform.system_prompt,
                self.config.transform.action_prompt,
                self.config.transform.transform_delimeters
            ),
            "TransformInQA": partial(
                llm.transform_qa,
                self.config.transform.llm_config,
                self.config.transform.system_prompt,
                self.config.transform.action_prompt,
                self.config.transform.transform_delimeters
            ),
            "TransformInSectionByHeader": section.transform_section_by_header,
            "TransformInSectionByType": partial(
                section.transform_section_by_type,
                self.config.transform.header_types
            ),
            "TransformInSectionByToc": partial(
                section.transform_section_by_toc,
                self.config.transform.toc_types,
                self.config.transform.toc_pattern
            ),
            "TransformInChunk": partial(
                chunk.transform_chunk,
                self.config.transform.chunk_size,
                self.config.transform.chunk_overlap,
                self.config.transform.token_chunk
            )
        })

    def _init_enrich_actions(self, action_map):
        if not self.config.enrich:
            self.config.enrich = CteActionRunnerDataTransformer.ConfigEnrich(**{})
        action_map["EnrichMetadata"] = partial(
            metadata.add_metadata,
            self.config.enrich.metadata
        )

    def process(
            self,
            actions: List[str],
            elements: List[Dict[str, Any]]
        ) -> 'CteActionRunnerDataTransformer.Result':
        """
        Perform the specified CTE actions on the provided elements.
        
        :param actiosn: List of actions to perform
        :param elements: Elements to transform
        :return: Result object containing the trasnformed elements
        """
        try:
            self.result.status = "success"
            for action in actions:
                action_function = self.action_map.get(action)
                if not action_function:
                    logger.error(f"Unknown action: {action}")
                    raise ValueError(f"Unknown action: {action}")
                logger.debug(f"Performing action: {action}")
                elements = action_function(elements)
            self.result.elements = elements
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while transforming the elements: {e}"
            logger.error(self.result.error_message)
        return self.result
    