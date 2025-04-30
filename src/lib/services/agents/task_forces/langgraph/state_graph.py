#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lang Graph Multi Agent AI Task Force

This module allows for:
- Initializing and returning the Lang Graph multi-agent system.
- Running a request on the system.
"""

import functools
import operator
from typing import Tuple, Annotated, Sequence, Optional, Any, Dict, List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import create_react_agent
from src.lib.core.log import Logger
from src.lib.services.chat.prompt_render import PromptRender
from src.lib.services.chat.model import ChatModel
from src.lib.services.agents.task_forces.base import BaseTaskForce


logger = Logger().get_logger()

AGENT_PROMPT_TEMPLATE = """
You are an intelligent agent. Your primary goal is to "{{ goal }}". To achieve this, your task is to "{{ task }}". 

Instructions:
1. Be resourceful and use any information or tools available to complete the task efficiently.
2. Ensure that all actions align with the primary goal.
3. Provide clear feedback or output at every step to ensure progress is visible.
4. If you encounter obstacles, adjust your approach, but remain focused on the goal.
"""

class AgentState(TypedDict):
    "The agent state is the input to each node in the graph"
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str


class LangGraphAgentTaskForce(BaseTaskForce):  # pylint: disable=R0903
    """
    LangGraph Multi Agent class
    """

    class Config(BaseTaskForce.Config):
        """
        Configuration for the Multi Agent class.
        """
        tasks: List["LangGraphAgentTaskForce.ConfigTask"] = Field(
            ...,
            description="List of tasks to be performed by agents"
        )
        recursion_limit: Optional[int] = Field(
            10,
            description="Limit to recursion inside the graph"
        )

    class ConfigTask(BaseTaskForce.ConfigTask):
        """
        Represents a task with a description, expected output, and associated agent.
        """
        agent: "LangGraphAgentTaskForce.ConfigAgent" = Field(
            ...,
            description="Agent responsible for the task"
        )

    class ConfigAgent(BaseTaskForce.ConfigAgent):
        """
        Represents an agent with specific roles, goals, and other attributes.
        """
        edges: Optional["LangGraphAgentTaskForce.ConfigEdges"] = Field(
            None,
            description="List of edges from this agent to the others"
        )

    class ConfigEdges(BaseModel):
        """
        Represents the edges that connect an agent with the others
        """
        nodes: List[str] = Field(
            ...,
            description="List of next agents, identified by their roles"
        )
        routing_function: Optional[Any] = Field(
            None,
            description=(
                "Function to handle the routing to the next agents."
                "Its input should be the graph state and the ouput the next agent role"
            )
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LangGraphAgentTaskForce with the given configuration.

        :param config: Configuration dictionary.
        """
        self.config = LangGraphAgentTaskForce.Config(**config)
        self.result = LangGraphAgentTaskForce.Result()
        self.llm = self._init_llm()
        self.graph = self._init_graph()

    def _init_llm(self) -> Any:
        """
        Initialize the language model.

        :return: Initialized language model.
        """
        chat_model = ChatModel.create(self.config.llm)
        result = chat_model.get_model()
        return result.model

    def _init_graph(self) -> StateGraph:
        """
        Initialize the graph with agents and tasks.

        :return: Compiled Graph object.
        """
        workflow = StateGraph(AgentState)
        self._add_nodes_to_graph(workflow)
        self._add_edges_to_graph(workflow)
        graph = workflow.compile()
        return graph

    def _add_nodes_to_graph(self, workflow: StateGraph) -> None:
        """
        Add nodes to the graph from the task configurations.
        
        :param workflow: The graph to which nodes will be added.
        """
        for task_config in self.config.tasks:
            node_name, node_obj = self._create_node(task_config)
            workflow.add_node(node_name, node_obj)

    def _create_node(self, task_config: BaseTaskForce.ConfigTask) -> Tuple[str, Any]:
        """
        Create a node based on the provided task configuration.

        :param task_config: Configuration for the task.
        :return: A tuple containing the agent's name and the initialized Node object.
        """
        agent_name = task_config.agent.role
        if task_config.agent.tools:
            agent = self._create_task_agent(task_config)
            node = functools.partial(self._agent_node, agent=agent, name=agent_name)
        else:
            agent = self._create_llm_agent(task_config)
            node = functools.partial(self._llm_node, agent=agent, name=agent_name)
        return agent_name, node

    def _create_task_agent(self, task_config: BaseTaskForce.ConfigTask) -> Any:
        """
        Create an agent based on the provided task confguration.

        :param task_config: Configuration for the task.
        :return: Initialized Agent object.
        """
        system_prompt = self._render_system_prompt(task_config)
        return create_react_agent(
            self.llm,
            tools=task_config.agent.tools,
            state_modifier=system_prompt
        )

    def _render_system_prompt(self, task_config: BaseTaskForce.ConfigTask) -> Any:
        """
        Render system prompt template with task information.

        :param task_config: Configuration for the task.
        :return: System prompt.
        """
        prompt_render = PromptRender.create({'type': 'JinjaTemplate'})
        system_prompt = prompt_render.render(
            AGENT_PROMPT_TEMPLATE,
            goal=task_config.agent.goal,
            task=task_config.description
        )
        return system_prompt.content

    def _agent_node(self, state: Any, agent: Any, name: str) -> Any:
        """
        Helper function that convert agent response in human message

        :param state: Graph state.
        :param agent: Agent object.
        :param name: Agent name.
        :return: Human message.
        """
        result = agent.invoke(state)
        logger.debug(f"{name}: {result['messages'][-1].content}")
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content)]
        }

    def _create_llm_agent(self, task_config: BaseTaskForce.ConfigTask) -> Any:
        """
        Create an LLM agent based on the provided task confguration.

        :param task_config: Configuration for the task.
        :return: Initialized Agent object.
        """
        system_prompt = self._render_system_prompt(task_config)
        return {
            "llm": self.llm,
            "system_prompt": system_prompt
        }

    def _llm_node(self, state: Any, agent: Any, name: str) -> Any:
        """
        Helper function that convert LLM agent response in human message

        :param state: Graph state.
        :param agent: Agent object.
        :param name: Agent name.
        :return: Human message.
        """
        messages = [SystemMessage(content=agent["system_prompt"])]
        messages += state["messages"]
        response = agent["llm"].invoke(messages)
        logger.debug(f"{name}: {response.content}")
        return {
            "messages": [HumanMessage(content=response.content)]
        }

    def _add_edges_to_graph(self, workflow: StateGraph) -> None:
        """
        Add edges to the graph based on the planning type.

        :param workflow: The graph to which edges will be added.
        """
        if self.config.plan_type == "Graph":
            self._add_custom_graph_edges(workflow)
        else:
            self._add_sequential_edges(workflow)

    def _add_sequential_edges(self, workflow: StateGraph) -> None:
        """
        Add sequential edges to the graph from 'START' to 'END'.

        :param workflow: The graph to which edges will be added.
        """
        if self.config.plan_type != "Sequential":
            logger.warning(f"No valid planning type '{self.config.plan_type}', set to 'Sequential'")
        agent_roles = [START] + [task.agent.role for task in self.config.tasks] + [END]
        for i in range(len(agent_roles) - 1):
            workflow.add_edge(agent_roles[i], agent_roles[i + 1])

    def _add_custom_graph_edges(self, workflow: StateGraph) -> None:
        """
        Add custom graph edges for non-sequential plans.

        :param workflow: The graph to which custom edges will be added.
        :raises ValueError: If the edge configuration is invalid.
        """
        agent_roles = [task.agent.role for task in self.config.tasks]
        # Add initial edge from START to the first agent role
        workflow.add_edge(START, agent_roles[0])
        for task in self.config.tasks:
            edges = task.agent.edges
            if not edges:
                raise ValueError(f"Edges must be defined for '{task.agent.role}' in Graph type.")
            if edges.routing_function:
                if len(edges.nodes) <= 1:
                    raise ValueError("At least 2 nodes are required if there's a routing function.")
                # Create a conditional map, replacing 'FINISH' with END
                conditional_map = {
                    node: (END if node == "FINISH" else node)
                    for node in edges.nodes
                }
                workflow.add_conditional_edges(
                    task.agent.role,
                    edges.routing_function,
                    conditional_map)
            else:
                if len(edges.nodes) != 1:
                    raise ValueError("Exactly 1 node must be defined if there's no routing.")
                next_node = edges.nodes[0]
                if edges.nodes[0] == "FINISH":
                    next_node = END
                workflow.add_edge(task.agent.role, next_node)

    def run(self, message: str) -> BaseTaskForce.Result:
        """
        Execute the graph with the input message.

        :param message: The input message to process.
        :return: The result of the execution, containing status and completion or error message.
        """
        try:
            self.result.status = "success"
            messages = [HumanMessage(content=message)]
            response = self.graph.invoke(
                {"messages": messages},
                {"recursion_limit": self.config.recursion_limit}
            )
            self.result.completion = response['messages'][-1].content
            self.result.metadata = response['messages']
            logger.debug(f"Prompt generated: {self.result.completion}")
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking the graph: {e}"
            logger.error(self.result.error_message)
        return self.result
