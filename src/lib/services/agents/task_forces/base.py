#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Model

Placeholder class that has to be overwritten.
"""

import abc
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class BaseTaskForce(abc.ABC):  # pylint: disable=R0903
    """
    Base Task Force
    """

    class Config(BaseModel):
        """
        Configuration for the Multi Agents class.
        """
        type: str = Field(
            ...,
            description="Type of the Multi AI Agent System"
        )
        plan_type: str = Field(
            ...,
            description="Type of the plan (e.g. Hierarchical or Sequential)"
        )
        tasks: List["BaseTaskForce.ConfigTask"] = Field(
            ...,
            description="List of tasks to be performed by agents"
        )
        llm: Dict[str, Any] = Field(
            None,
            description="Configuration settings for the LLM"
        )
        verbose: Optional[bool] = Field(
            True,
            description="Verbose flag"
        )

    class ConfigTask(BaseModel):
        """
        Represents a task with a description, expected output, and associated agent.
        """
        description: str = Field(
            ...,
            description="Description of the task"
        )
        agent: "BaseTaskForce.ConfigAgent" = Field(
            ...,
            description="Agent responsible for the task"
        )

    class ConfigAgent(BaseModel):
        """
        Represents an agent with specific roles, goals, and other attributes.
        """
        role: str = Field(
            ...,
            description="Role of the agent"
        )
        goal: str = Field(
            ...,
            description="Goal of the agent"
        )
        tools: Optional[List[Any]] = Field(
            [],
            description="List of tools available to the agent"
        )

    class Result(BaseModel):
        """
        Result of the task force invocation.
        """
        status: str = Field(
            default="success",
            description="Status of the operation, e.g., 'success' or 'failure'."
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Detailed error message if the operation failed."
        )
        completion: Optional[str] = Field(
            None,
            description="Completion of the reasoning process."
        )
        metadata: Optional[str] = Field(
            None,
            description="Metadata related to the operations."
        )

    @abc.abstractmethod
    def run(self, message: str) -> 'BaseTaskForce.Result':
        """
        Run the multi-agent task force.

        :param message: Message to be processed by the task force.
        :return: Result object containing the outcome of the reasoning process.
        """
