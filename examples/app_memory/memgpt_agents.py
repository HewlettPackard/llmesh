#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MemGPT Agents

This module implements the agents for saving and retrieving memories

Note: Derived by Lang-MemGPT (repo: https://github.com/langchain-ai/lang-memgpt)
"""

import asyncio
from datetime import datetime, timezone
from typing import List
from typing_extensions import Literal, Annotated, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AnyMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages.utils import get_buffer_string
from langchain_core.runnables.config import (
    RunnableConfig,
    get_executor_for_config,
)
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from self_serve_platform.chat.prompt_render import PromptRender
from self_serve_platform.chat.model import ChatModel
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger
from examples.app_memory.memgpt_tools import (
    search_memory,
    save_recall_memory,
    save_core_memory,
    fetch_core_memories
)


# Parse command-line arguments and start the application
PATH = 'examples/app_memory/'
CONFIG = Config(PATH+'config.yaml').get_settings()

PROMPT_CONFIG = CONFIG["prompts"]
MODEL_CONFIG = CONFIG["llm"]
MEMORY_CONFIG = CONFIG["memory"]["core"]
STORAGE_CONFIG = CONFIG["memory"]["recall"]["storage"]
LOADER_CONFIG = CONFIG["memory"]["recall"]["loader"]
RETRIEVER_CONFIG = CONFIG["memory"]["recall"]["retriever"]

# Create Logger
logger = Logger().configure(CONFIG["logger"]).get_logger()

# Combine all tools
all_tools = [search_memory, save_recall_memory, save_core_memory]

# Define the prompt template for the agent
def _render_prompt():
    prompt_render = PromptRender.create(PROMPT_CONFIG)
    result = prompt_render.load(
        "system_prompt",
        core_memories = "{core_memories}",
        recall_memories = "{recall_memories}",
        current_time =  "{current_time}")
    return result.content
prompt = ChatPromptTemplate.from_messages([
    ("system", _render_prompt()),
    ("placeholder", "{messages}"),
])

class GraphConfig(TypedDict):
    "Define the schema for the graph"
    model: str | None
    """The model to use for the memory assistant."""
    thread_id: str
    """The thread ID of the conversation."""
    user_id: str
    """The ID of the user to remember in the conversation."""


class StateConfig(TypedDict):
    "Define the schema for the state maintained throughout the conversation"
    messages: Annotated[List[AnyMessage], add_messages]
    """The messages in the conversation."""
    core_memories: List[str]
    """The core memories associated with the user."""
    recall_memories: List[str]
    """The recall memories retrieved for the current context."""


async def agent(state: StateConfig) -> StateConfig:
    """Process the current state and generate a response using the LLM.

    Args:
        state (StateConfig): The current state of the conversation.

    Returns:
        StateConfig: The updated state with the agent's response.
    """
    llm = _get_llm()
    bound = prompt | llm.bind_tools(all_tools)
    core_str = (
        "<core_memory>\n" + "\n".join(state["core_memories"]) + "\n</core_memory>"
    )
    recall_str = (
        "<recall_memory>\n" + "\n".join(state["recall_memories"]) + "\n</recall_memory>"
    )
    prediction = await bound.ainvoke(
        {
            "messages": state["messages"],
            "core_memories": core_str,
            "recall_memories": recall_str,
            "current_time": datetime.now(tz=timezone.utc).isoformat(),
        }
    )
    return {"messages": prediction}

def _get_llm():
    chat_model = ChatModel.create(MODEL_CONFIG)
    result = chat_model.get_model()
    return result.model

def load_memories(state: StateConfig, config: RunnableConfig) -> StateConfig:
    """Load core and recall memories for the current conversation.

    Args:
        state (StateConfig): The current state of the conversation.
        config (RunnableConfig): The runtime configuration for the agent.

    Returns:
        StateConfig: The updated state with loaded memories.
    """
    convo_str = get_buffer_string(state["messages"])
    with get_executor_for_config(config) as executor:
        futures = [
            executor.submit(fetch_core_memories),
            executor.submit(search_memory.invoke, convo_str),
        ]
        core_memories = futures[0].result()
        recall_memories = futures[1].result()
    return {
        "core_memories": core_memories,
        "recall_memories": recall_memories,
    }


def route_tools(state: StateConfig) -> Literal["tools", "__end__"]:
    """Determine whether to use tools or end the conversation based on the last message.

    Args:
        state (StateConfig): The current state of the conversation.

    Returns:
        Literal["tools", "__end__"]: The next step in the graph.
    """
    msg = state["messages"][-1]
    if msg.tool_calls:
        return "tools"
    return END


# Create the graph and add nodes
builder = StateGraph(StateConfig, GraphConfig)
builder.add_node(load_memories)
builder.add_node(agent)
builder.add_node("tools", ToolNode(all_tools))

# Add edges to the graph
builder.add_edge(START, "load_memories")
builder.add_edge("load_memories", "agent")
builder.add_conditional_edges("agent", route_tools)
builder.add_edge("tools", "agent")

# Compile the graph
memgraph = builder.compile()


async def chat(message):
    "Testing main"
    logger.info('Testing MemGPT...')
    messages = [HumanMessage(content=message)]
    response = await memgraph.ainvoke(
        {"messages": messages},
        {"recursion_limit": 10},
        debug=True
    )
    logger.debug(f"COMPLETION:\n\t{response['messages'][-1].content}")
    logger.debug(f"METADATA:\n\t{response['messages'][-1].response_metadata}")


if __name__ == '__main__':
    # Test Graph
    asyncio.run(chat("hi"))
    asyncio.run(chat("my name is Gino"))
    asyncio.run(chat("i like play soccer"))
