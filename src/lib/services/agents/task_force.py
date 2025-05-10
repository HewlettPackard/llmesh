#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Task Force Module

This module defines the TaskForce class and associated class for 
managing different Agentic AIs. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.agents.task_forces.crewai.crew import (
    CrewAIMultiAgentTaskForce)
from src.lib.services.agents.task_forces.langgraph.state_graph import (
    LangGraphAgentTaskForce)


class TaskForce:  # pylint: disable=R0903
    """
    A task force class that uses a factory pattern to return
    the selected multi AI agent system.
    """

    _agents: Dict[str, Type] = {
        'CrewAIMultiAgent': CrewAIMultiAgentTaskForce,
        'LangGraphMultiAgent': LangGraphAgentTaskForce,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return the appropriate Task Force based on the provided configuration.

        :param config: Configuration dictionary containing the type of task force.
        :return: An instance of the selected task force.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        agents_type = config.get('type')
        if not agents_type:
            raise ValueError("Configuration must include 'type'.")
        agents_class = TaskForce._agents.get(agents_type)
        if not agents_class:
            raise ValueError(f"Unsupported extractor type: {agents_type}")
        return agents_class(config)
