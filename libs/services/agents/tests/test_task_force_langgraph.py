#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the TaskForce factory and its model flavors,
specifically the LangGraphAgentTaskForce.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate model types based on the given configuration. It also tests the specific behavior of 
each model's methods to ensure correct setup and functionality.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from langchain_core.messages import  HumanMessage
from libs.services.agents.task_force import TaskForce
from libs.services.agents.task_forces.langgraph.state_graph import (
    LangGraphAgentTaskForce)


# Mock configurations for testing
@pytest.mark.parametrize("expected_config, expected_class", [
    (
        {
            'type': 'LangGraphMultiAgent',
            'tasks': [
                {
                    'description': 'Test Task 1',
                    'expected_output': 'Output 1',
                    'human_input': False,
                    'agent': {
                        'role': 'Tester',
                        'goal': 'Test the system',
                        'edges': None,  # Assuming edges can be None
                        'tools': []
                    }
                }
            ],
            'llm': {
                "type": "LangChainChatOpenAI",
                "model_name": "gpt-3.5-turbo",
                "api_key": "your_api_key"
            },
            'plan_type': 'Sequential',
            'verbose': True
        },
        LangGraphAgentTaskForce
    ),
])
def test_create(expected_config, expected_class):
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    task_force_instance = TaskForce.create(expected_config)
    assert isinstance(task_force_instance, expected_class)


def test_create_with_invalid_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when an unsupported type is passed.
    """
    with pytest.raises(ValueError):
        TaskForce.create({"type": "UnknownType"})


def test_create_with_missing_type():
    """
    Test the create factory method to ensure it raises a ValueError
    when the 'type' key is missing in the configuration.
    """
    with pytest.raises(ValueError):
        TaskForce.create({})


# Mock configuration for LangGraphAgentTaskForce
config = {
    'type': 'LangGraphMultiAgent',
    'tasks': [
        {
            'description': 'Test Task 1',
            'expected_output': 'Output 1',
            'human_input': False,
            'agent': {
                'role': 'Tester',
                'goal': 'Test the system',
                'edges': None,  # Edges can be None for Sequential plan_type
                'tools': []
            }
        }
    ],
    'llm': {
        "type": "LangChainChatOpenAI",
        "model_name": "gpt-3.5-turbo",
        "api_key": "your_api_key"
    },
    'plan_type': 'Sequential',
    'verbose': True
}
@patch.object(LangGraphAgentTaskForce, '_init_llm', return_value=MagicMock())
@patch.object(LangGraphAgentTaskForce, '_init_graph')
def test_langgraph_agent_task_force_run(mock_init_llm, mock_init_graph):  # pylint: disable=W0613
    """
    Test the run method of LangGraphAgentTaskForce to ensure it executes correctly
    and returns the expected result.
    """
    # Create a mock graph that returns a predefined response
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        'messages': [MagicMock(content="Mocked completion response")]
    }
    mock_init_graph.return_value = mock_graph
    # Initialize the LangGraphAgentTaskForce
    task_force = LangGraphAgentTaskForce(config)
    # Ensure that the graph attribute is set correctly
    task_force.graph = mock_graph
    # Run the task force with a test message
    result = task_force.run("Test message")
    # Assert the result status and completion
    assert result.status == "success"
    assert result.completion == "Mocked completion response"
    assert isinstance(result.metadata, list)
    mock_graph.invoke.assert_called_once_with(
        {"messages": [HumanMessage(content="Test message")]},
        {"recursion_limit": task_force.config.recursion_limit}
    )


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
