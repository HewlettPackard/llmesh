#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module re-exports key functionalities related to Agents handling
within the lib. It simplifies the import for clients 
of the lib package.

The package name 'athon' is a shorthand for 'agentic-python', reflecting
its focus on building and managing agentic behaviors in Python-based systems.
"""

from src.lib.services.agents.reasoning_engine import ReasoningEngine
from src.lib.services.agents.task_force import TaskForce
from src.lib.services.agents.tool_repository import ToolRepository


__all__ = [
    'ReasoningEngine',
    'TaskForce',
    'ToolRepository'
]
