#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This pytest script tests the TaskForce factory and its model flavors, CrewAIMultiAgentTaskForce.
The tests ensure that the factory method correctly initializes and returns instances of the 
appropriate model types based on the given configuration. It also tests the specific behavior of 
each model's methods to ensure correct setup and functionality.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from libs.services.agents.task_force import TaskForce
from libs.services.agents.task_forces.crewai.crew import CrewAIMultiAgentTaskForce


# Mock configurations for testing
@pytest.mark.parametrize("config, expected_class", [
    (
        {
            'type': 'CrewAIMultiAgent',
            'tasks': [
                {
                    'description': 'Test Task 1',
                    'expected_output': 'Output 1',
                    'human_input': False,
                    'agent': {
                        'role': 'Tester',
                        'goal': 'Test the system',
                        'backstory': 'A diligent tester',
                        'allow_delegation': True,
                        'tools': []
                    }
                }
            ],
            'llm': {
                "type": "LangChainChatOpenAI",
                "model_name": "gpt-3",
                "api_key": "your_api_key"
            },
            'plan_type': 'Sequential',
            'verbose': True
        },
        CrewAIMultiAgentTaskForce
    ),
])

def test_create(config, expected_class):  # pylint: disable=W0621
    """
    Test the create factory method to ensure it returns instances of the correct classes
    based on the configuration provided.
    """
    task_force_instance = TaskForce.create(config)
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


# Mock configuration for CrewAIMultiAgentTaskForce
config = {
    'type': 'CrewAIMultiAgent',
    'tasks': [
        {
            'description': 'Test Task 1',
            'expected_output': 'Output 1',
            'human_input': False,
            'agent': {
                'role': 'Tester',
                'goal': 'Test the system',
                'backstory': 'A diligent tester',
                'allow_delegation': True,
                'tools': []
            }
        }
    ],
    'llm': {
                "type": "LangChainChatOpenAI",
                "model_name": "gpt-3",
                "api_key": "your_api_key"
    },
    'plan_type': 'Sequential',
    'verbose': True
}

@patch.object(CrewAIMultiAgentTaskForce, '_init_llm', return_value=MagicMock())
@patch.object(CrewAIMultiAgentTaskForce, '_init_crew')
def test_crewai_multi_agent_task_force_run(mock_init_llm, mock_init_crew):  # pylint: disable=W0613
    """
    Test the run method of CrewAIMultiAgentTaskForce to ensure it executes correctly
    and returns the expected result.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.raw = "Mocked completion response"
    mock_response.token_usage = {"key": "value"}
    # Mock the crew kickoff method
    mock_crew = MagicMock()
    mock_crew.kickoff.return_value = mock_response
    mock_init_crew.return_value = mock_crew
    # Initialize the CrewAIMultiAgentTaskForce
    task_force = CrewAIMultiAgentTaskForce(config)
    # Ensure that the crew attribute is set correctly
    task_force.crew = mock_crew
    # Run the task force with a test message
    result = task_force.run("Test message")
    # Assert the result status and completion
    assert result.status == "success"
    assert result.completion == "Mocked completion response"
    assert result.metadata == {"key": "value"}
    mock_crew.kickoff.assert_called_once_with(inputs={'request': "Test message"})


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv'])
