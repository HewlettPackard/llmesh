#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for TaskForce using CrewAIMultiAgent and LangGraphMultiAgent configurations.

This test file includes two TaskForce configurations:
1. CrewAIMultiAgent: A sequential multi-agent task force that generates a blog post outline,
     writes the content, and optimizes it for SEO.
2. LangGraphMultiAgent: A graph-based multi-agent task force that uses conditional branching
    for task execution, with agents responsible for outlining, content development,
    and SEO optimization.

To run these tests, use:
    pytest -m "integration and agents"
"""

import os
import pytest
from langchain_community.tools.tavily_search import TavilySearchResults
from athon.agents import TaskForce


tavily_tool = TavilySearchResults(max_results=1)

SHORT_EXECUTION = False

# Common Task descriptions and outputs
TASK1_DESCRIPTION = """
Generate a structured outline for a blog post on {request} based on the research. Max 3 items.
"""
TASK1_EXPECTED_OUTPUT = """
A detailed blog post outline with 3-5 main sections.
"""
TASK2_DESCRIPTION = """
Develop a complete blog post including an introduction, main content, and conclusion. Max 50 words.
"""
TASK2_EXPECTED_OUTPUT = """
A full blog post of around 500-800 words.
"""
# Common agent roles, goals, and backstories
TASK1_AGENT_ROLE = "Outline Agent"
TASK1_AGENT_GOAL = "Create a comprehensive blog post outline"
TASK1_AGENT_BACKSTORY = "Expert in structuring content into engaging and informative blog outlines"
TASK2_AGENT_ROLE = "Content Development Agent"
TASK2_AGENT_GOAL = "Write a well-researched blog post with intro, body, and conclusion"
TASK2_AGENT_BACKSTORY = "Skilled at turning outlines into engaging and coherent blog posts"
# Common LLM Configuration
LLM_CONFIG = {
    'type': 'LangChainChatOpenAI',
    'api_key': os.getenv("OPENAI_API_KEY"),
    'model_name': "gpt-4o-mini"
}
# Base Task Force Configuration Template (common structure)
BASE_TASK_FORCE_CONFIG = {
    'plan_type': 'Sequential',  # This will be overridden in the specific configurations
    'tasks': [
        {
            'description': TASK1_DESCRIPTION,
            'expected_output': TASK1_EXPECTED_OUTPUT,
            'agent': {
                'role': TASK1_AGENT_ROLE,
                'goal': TASK1_AGENT_GOAL,
                'backstory': TASK1_AGENT_BACKSTORY,
                'tools': [tavily_tool]
            }
        },
        {
            'description': TASK2_DESCRIPTION,
            'expected_output': TASK2_EXPECTED_OUTPUT,
            'agent': {
                'role': TASK2_AGENT_ROLE,
                'goal': TASK2_AGENT_GOAL,
                'backstory': TASK2_AGENT_BACKSTORY,
                'tools': []
            }
        }
    ],
    'llm': LLM_CONFIG,
    'verbose': True,
    'memory': False
}


@pytest.fixture
def crewai_task_force():
    """
    Fixture to initialize and return an instance of TaskForce with
    the CrewAIMultiAgent configuration.
    """
    crewai_config = BASE_TASK_FORCE_CONFIG.copy()
    crewai_config.update({
        'type': 'CrewAIMultiAgent',
    })
    return TaskForce.create(crewai_config)

@pytest.mark.integration
@pytest.mark.agents
def test_crewai_task_force_run(crewai_task_force):  # pylint: disable=W0621
    """
    Test the execution of the CrewAIMultiAgent TaskForce.
    Verifies that the TaskForce completes successfully with the given input message.
    """
    input_message = "Write a blog post about the importance of renewable energy."
    # Run the task force
    result = crewai_task_force.run(input_message)
    # Assert that the result is successful
    assert result.status == "success", f"TaskForce failed: {result.error_message}"
    assert result.completion is not None, "TaskForce result should contain a completion"
    print(f"COMPLETION:\n{result.completion}")


@pytest.fixture
def langgraph_task_force():
    """
    Fixture to initialize and return an instance of TaskForce
    with the LangGraphMultiAgent configuration.
    """
    def should_end(state):
        """
        Conditional function for task routing.
        """
        print(f"\n\nSTATE:\n{state}\n\n")
        if SHORT_EXECUTION:
            return 'FINISH'
        return 'Content Development Agent'

    langraph_config = BASE_TASK_FORCE_CONFIG.copy()
    langraph_config.update({
        'type': 'LangGraphMultiAgent',
        'plan_type': 'Graph',  # Override the plan type
        'tasks': [
            {
                'description': TASK1_DESCRIPTION,
                'agent': {
                    'role': TASK1_AGENT_ROLE,
                    'goal': TASK1_AGENT_GOAL,
                    'tools': [tavily_tool],
                    'edges': {
                        'routing_function': should_end,
                        'nodes': [TASK2_AGENT_ROLE, 'FINISH']
                    }
                }
            },
            {
                'description': TASK2_DESCRIPTION,
                'agent': {
                    'role': TASK2_AGENT_ROLE,
                    'goal': TASK2_AGENT_GOAL,
                    'tools': [],
                    'edges': {
                        'nodes': ['FINISH']
                    }
                }
            }
        ]
    })
    return TaskForce.create(langraph_config)

@pytest.mark.integration
@pytest.mark.agents
def test_langgraph_task_force_run(langgraph_task_force):  # pylint: disable=W0621
    """
    Test the execution of the LangGraphMultiAgent TaskForce.
    Verifies that the TaskForce completes successfully or follows the conditional branching.
    """
    input_message = "Write a blog post about the importance of renewable energy."
    # Run the task force
    result = langgraph_task_force.run(input_message)
    # Assert that the result is successful
    assert result.status == "success", f"TaskForce failed: {result.error_message}"
    assert result.completion is not None, "TaskForce result should contain a completion"
    print(f"COMPLETION:\n{result.completion}")


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    pytest.main([current_file, '-vv', '-m', 'integration and agents'])
