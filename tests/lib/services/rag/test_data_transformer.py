#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the DataTransformer factory and its transformer flavor, 
CteActionRunnerDataTransformer, in the data transformer module.
The tests ensure that the factory method correctly initializes and returns 
instances of the appropriate transformer types based on the given configuration.
It also tests the behavior of the transformer's process method to ensure correct 
transformation of document elements.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from src.lib.services.rag.data_transformer import DataTransformer
from src.lib.services.rag.data_transformers.cte_action_runner import (
    CteActionRunnerDataTransformer)


@pytest.mark.parametrize("config, expected_class", [
    (
        {"type": "CteActionRunner", "clean": {}, "transform": {}, "enrich": {}},
        CteActionRunnerDataTransformer
    )
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    transformer_instance = DataTransformer.create(config)
    assert isinstance(transformer_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        DataTransformer.create({"type": "InvalidType"})


@pytest.fixture
def cte_action_runner_config():
    """
    Mockup CteActionRunnerDataTransformer configuration.
    """
    return {
        "type": "CteActionRunner",
        "clean": {
            "fields": ["header", "text"],
            "headers_to_remove": ["UnwantedHeader"],
            "min_section_length": 50
        },
        "transform": {
            "llm_config": {"model_name": "gpt-3"},
            "system_prompt": "Summarize the following document:",
            "action_prompt": "Provide a summary.",
            "transform_delimeters": ['```', '```json'],
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "token_chunk": 256
        },
        "enrich": {
            "metadata": {"source": "document_1"}
        }
    }


@patch('src.lib.services.rag.data_transformers.cte_action_runner.Logger.get_logger')
def test_process_success(mock_get_logger, cte_action_runner_config):  # pylint: disable=W0621
    """
    Test the process method of CteActionRunnerDataTransformer to verify it performs
    the transformations correctly and returns the expected result.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    transformer = CteActionRunnerDataTransformer(cte_action_runner_config)
    elements = [
        {
            "text": "This is a text.",
            "metadata": {"page": 1, "header": "Header1"}
        },
        {
            "text": "This section should be removed.",
            "metadata": {"page": 2, "header": "UnwantedHeader"}
        },
    ]
    actions = ["RemoveSectionsByHeader"]
    result = transformer.process(actions, elements)
    assert result.status == "success"
    assert len(result.elements) == 1  # Only one element should remain after filtering
    assert result.elements[0]["metadata"]["header"] == "Header1"


@patch('src.lib.services.rag.data_transformers.cte_action_runner.Logger.get_logger')
def test_process_unknown_action(mock_get_logger, cte_action_runner_config):  # pylint: disable=W0621
    """
    Test the process method of CteActionRunnerDataTransformer 
    to ensure it handles unknown actions gracefully.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    transformer = CteActionRunnerDataTransformer(cte_action_runner_config)
    elements = [
        {"text": "This is a text.", "metadata": {"header": "Header1", "page": 1}},
    ]
    actions = ["UnknownAction"]
    result = transformer.process(actions, elements)
    assert result.status == "failure"
    assert "Unknown action" in result.error_message


@patch('src.lib.services.rag.data_transformers.cte_action_runner.Logger.get_logger')
def test_process_failure(mock_get_logger, cte_action_runner_config):  # pylint: disable=W0621
    """
    Test the process method of CteActionRunnerDataTransformer 
    to ensure it handles exceptions correct and logs the appropriate error message.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    transformer = CteActionRunnerDataTransformer(cte_action_runner_config)
    elements = [
        {"header": "Header1", "text": "This is a text.", "metadata": {"page": 1}},
    ]
    actions = ["RemoveSectionsByHeader"]
    # Simulate an exception during processing
    with patch.object(
            transformer,
            'action_map',
            {'RemoveSectionsByHeader': MagicMock(side_effect=Exception("Test error"))}):
        result = transformer.process(actions, elements)
        assert result.status == "failure"
        assert "An error occurred while transforming the elements" in result.error_message


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
