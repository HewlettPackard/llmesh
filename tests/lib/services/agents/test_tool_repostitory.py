#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the ToolRepository factory and its repository flavor,
LangChainStructuredToolRepository. The tests ensure that the factory method correctly
initializes and returns instances of the appropriate repository types based on the
given configuration. It also tests the specific behavior of each repository's methods to ensure
correct setup and functionality.
"""

import os
from unittest.mock import MagicMock
import pytest
from src.lib.services.agents.tool_repositories.langchain.structured_tool import (
    LangChainStructuredToolRepository)
from src.lib.services.agents.tool_repository import ToolRepository


@pytest.fixture(autouse=True)
def reset_singleton():
    """
    Fixture to reset the singleton instance of LangChainStructuredToolRepository before each test.
    """
    LangChainStructuredToolRepository._instance = None  # pylint: disable=W0212


@pytest.mark.parametrize("config, expected_class", [
    (
        {
            "type": "LangChainStructured",
        },
        LangChainStructuredToolRepository
    )
])
def test_create(config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    repository_instance = ToolRepository.create(config)
    assert isinstance(repository_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        ToolRepository.create({"type": "UnknownType"})


@pytest.fixture
def mock_structured_tool():
    """
    Create a mock StructuredTool object.
    """
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    return mock_tool

def test_add_tool(mock_structured_tool):  # pylint: disable=W0621
    """
    Test the add_tool method of LangChainStructuredToolRepository to verify it adds tools correctly.
    """
    # Initialize the repository
    repository = LangChainStructuredToolRepository()
    # Add the mock tool
    result = repository.add_tool(mock_structured_tool)
    # Assert the tool was added successfully
    assert result.status == "success"
    assert len(repository._tools) == 1  # pylint: disable=W0212
    assert repository._tools[0] == mock_structured_tool  # pylint: disable=W0212
    assert repository._metadata.get(mock_structured_tool.name) is None  # pylint: disable=W0212
    # If you want to test with metadata, you can add this:
    metadata = {"key": "value"}
    repository.add_tool(mock_structured_tool, metadata)
    assert repository._metadata[mock_structured_tool.name] == metadata  # pylint: disable=W0212


def test_get_tools_no_filter(mock_structured_tool):  # pylint: disable=W0621
    """
    Test the get_tools method of LangChainStructuredToolRepository
    to verify it returns all tools when no filter is applied.
    """
    repository = LangChainStructuredToolRepository()
    repository.add_tool(mock_structured_tool)
    result = repository.get_tools()
    assert result.status == "success"
    assert len(result.tools) == 1


def test_get_tools_with_filter(mock_structured_tool):  # pylint: disable=W0621
    """
    Test the get_tools method of LangChainStructuredToolRepository
    to verify it filters tools correctly based on metadata.
    """
    repository = LangChainStructuredToolRepository()
    repository.add_tool(mock_structured_tool, metadata={"category": "test"})
    filtered_result = repository.get_tools(metadata_filter={"category": "test"})
    assert filtered_result.status == "success"
    assert len(filtered_result.tools) == 1
    filtered_result = repository.get_tools(metadata_filter={"category": "nonexistent"})
    assert filtered_result.status == "success"
    assert len(filtered_result.tools) == 0


def test_update_tool_success(mock_structured_tool):  # pylint: disable=W0621
    """
    Test the update_tool method of LangChainStructuredToolRepository
    to verify it updates a tool's configuration and metadata successfully.
    """
    repository = LangChainStructuredToolRepository()
    repository.add_tool(mock_structured_tool, metadata={"category": "test"})
    # Update the tool's configuration and metadata
    new_mock_tool = MagicMock()
    new_mock_tool.name = "test_tool"  # Same name as the existing tool
    new_metadata = {"category": "updated_test"}
    result = repository.update_tool("test_tool", new_tool=new_mock_tool, new_metadata=new_metadata)
    # Verify update was successful
    assert result.status == "success"
    assert repository._tools[0] == new_mock_tool  # pylint: disable=W0212
    assert repository._metadata["test_tool"] == new_metadata  # pylint: disable=W0212


def test_update_tool_metadata_only(mock_structured_tool):  # pylint: disable=W0621
    """
    Test the update_tool method to verify it updates only the metadata of a tool.
    """
    repository = LangChainStructuredToolRepository()
    repository.add_tool(mock_structured_tool, metadata={"category": "test"})
    # Update only the metadata
    new_metadata = {"category": "updated_test"}
    result = repository.update_tool("test_tool", new_metadata=new_metadata)
    # Verify metadata update was successful
    assert result.status == "success"
    assert repository._tools[0] == mock_structured_tool  # pylint: disable=W0212
    assert repository._metadata["test_tool"]["category"] == "updated_test"  # pylint: disable=W0212


def test_update_tool_not_found():
    """
    Test the update_tool method to verify it returns a failure status if the tool is not found.
    """
    repository = LangChainStructuredToolRepository()
    # Attempt to update a non-existent tool
    result = repository.update_tool("nonexistent_tool", new_metadata={"category": "updated_test"})
    # Verify the update failed with an appropriate error message
    assert result.status == "failure"
    assert "Tool 'nonexistent_tool' not found" in result.error_message


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
