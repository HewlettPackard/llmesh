#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CrewAI Multi Agent AI Task Force

This module allows for:
- Initializing and returning the Crew AI multi-agent system.
- Running a request on the system.
"""

from typing import Optional, Any, Dict, List, Union
from pydantic import Field
from crewai import Agent, Crew, Task, Process
from src.lib.core.log import Logger
from src.lib.services.chat.model import ChatModel
from src.lib.services.agents.task_forces.base import BaseTaskForce


logger = Logger().get_logger()


class CrewAIMultiAgentTaskForce(BaseTaskForce):  # pylint: disable=R0903
    """
    CrewAI Multi Agent class
    """

    class Config(BaseTaskForce.Config):
        """
        Configuration for the Multi Agent class.
        """
        tasks: List["CrewAIMultiAgentTaskForce.ConfigTask"] = Field(
            ...,
            description="List of tasks to be performed by agents"
        )
        memory: Optional[bool] = Field(
            False,
            description="Memory flag"
        )

    class ConfigTask(BaseTaskForce.ConfigTask):
        """
        Represents a task with a description, expected output, and associated agent.
        """
        expected_output: str = Field(
            ...,
            description="Expected output of the task"
        )
        agent: "CrewAIMultiAgentTaskForce.ConfigAgent" = Field(
            ...,
            description="Agent responsible for the task"
        )
        human_input: Optional[bool] = Field(
            False,
            description="Indicates if human input is required"
        )
        dependencies: Optional[List[Any]] = Field(
            None,
            description="List of context data or tasks"
        )
        output_schema: Optional[Any] = Field(
            None,
            description="Used to define or store the output schema/model"
        )

    class ConfigAgent(BaseTaskForce.ConfigAgent):
        """
        Represents an agent with specific roles, goals, and other attributes.
        """
        backstory: str = Field(
            ...,
            description="Backstory of the agent"
        )
        allow_delegation: Optional[bool] = Field(
            False,
            description="Indicates if the agent is allowed to delegate tasks"
        )
        max_iterations: Optional[int] = Field(
            2,
            description="Max iteration before answer"
        )
        max_execution_time: Optional[int] = Field(
            30,
            description="Max execution time before answer"
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the CrewAIMultiAgentTaskForce with the given configuration.

        :param config: Configuration dictionary.
        """
        self.config = CrewAIMultiAgentTaskForce.Config(**config)
        self.result = CrewAIMultiAgentTaskForce.Result()
        self.llm = self._init_llm()
        self.crew = self._init_crew()

    def _init_llm(self) -> Any:
        """
        Initialize the language model.

        :return: Initialized language model.
        """
        chat_model = ChatModel.create(self.config.llm)
        result = chat_model.get_model()
        return result.model

    def _init_crew(self) -> Crew:
        """
        Initialize the crew with agents and tasks.

        :return: Initialized Crew object.
        """
        agents = [
            self._create_agent(task_config.agent)
            for task_config in self.config.tasks
        ]
        tasks = [
            self._create_task(task_config, agents[i])
            for i, task_config in enumerate(self.config.tasks)
        ]
        return self._create_crew(agents, tasks)

    def _create_agent(self, agent_config: BaseTaskForce.ConfigAgent) -> Agent:
        """
        Create an agent based on the provided configuration.

        :param agent_config: Configuration for the agent.
        :return: Initialized Agent object.
        """
        return Agent(
            role=agent_config.role,
            goal=agent_config.goal,
            verbose=True,
            backstory=agent_config.backstory,
            tools=agent_config.tools,
            allow_delegation=agent_config.allow_delegation,
            max_iter=agent_config.max_iterations,
            max_execution_time=agent_config.max_execution_time,
            llm=self.llm
        )

    def _create_task(self, task_config: BaseTaskForce.ConfigTask, agent: Agent) -> Task:
        """
        Create a task based on the provided configuration.

        :param task_config: Configuration for the task.
        :param agent: Agent associated with the task.
        :return: Initialized Task object.
        """
        task_args = {
            "description": task_config.description,
            "expected_output": task_config.expected_output,
            "human_input": task_config.human_input,
            "agent": agent
        }
        if task_config.dependencies is not None:
            task_args["context"] = task_config.dependencies
        if task_config.output_schema is not None:
            task_args["output_pydantic"] = task_config.output_schema
        return Task(**task_args)

    def _create_crew(self, agents: List[Agent], tasks: List[Task]) -> Crew:
        """
        Create a crew based on the provided agents and tasks.

        :param agents: List of agents.
        :param tasks: List of tasks.
        :return: Initialized Crew object.
        """
        plan_type = self.config.plan_type
        params = {
            "agents": agents,
            "tasks": tasks,
            "memory": self.config.memory,
            "verbose": self.config.verbose,
            "process": self._get_process(plan_type)
        }
        if plan_type == "Hierarchical":
            params["manager_llm"] = self.llm
        return Crew(**params)

    def _get_process(self, plan_type: str) -> Process:
        """
        Get the process type based on the plan type.

        :param plan_type: Plan type as a string.
        :return: Process type.
        """
        process_mapping = {
            "Hierarchical": Process.hierarchical,
            "Sequential": Process.sequential
        }
        process = process_mapping.get(plan_type, Process.sequential)
        if process == Process.sequential and plan_type not in process_mapping:
            logger.warning(f"No valid planning type '{plan_type}', set to 'Sequential'")
        return process

    def run(self, message: Optional[Union[str, Dict[str, Any]]]) -> BaseTaskForce.Result:
        """
        Execute the crew with the input message.

        :param message: The input message to process.
        :return: The result of the execution, containing status and completion or error message.
        """
        try:
            self.result.status = "success"
            if isinstance(message, str):
                input_dict = {"request": message}
            elif isinstance(message, dict):
                input_dict = message
            else:
                raise ValueError(f"Invalid input message type: {type(message)}")
            response = self.crew.kickoff(inputs=input_dict)
            self.result.completion = response.raw
            self.result.metadata = response.token_usage
            logger.debug(f"Prompt generated: {self.result.completion}")
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking the crew: {e}"
            logger.error(self.result.error_message)
        return self.result
