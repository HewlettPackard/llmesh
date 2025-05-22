#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reasoning Engine for HPE Athonet LLM Platform

This script is the core of the HPE Athonet LLM Platform's reasoning engine, integrating 
various AI and language processing tools to create an interactive, AI-powered assistant. 
The engine is built using LLM models, augmented with custom plugins for 
specialized tasks. It features dynamic plugin loading, conversational memory management, 
and a modular architecture for easily incorporating additional functionalities. 
The engine's primary purpose is to process user inputs and generate intelligent, 
context-aware responses, making it a versatile tool for various 
applications in data analysis, automated assistance, and interactive querying.
"""

from typing import Dict, Any, List, Optional
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool
from src.lib.core.log import Logger
from src.lib.services.chat.model import ChatModel
from src.lib.services.chat.memory import ChatMemory
from src.lib.services.agents.tool_repository import ToolRepository
from src.lib.services.agents.reasoning_engines.base import BaseReasoningEngine


logger = Logger().get_logger()


class LangChainAgentExecutor(BaseReasoningEngine):
    """
    A central component of Athon, the ReasoningEngine class orchestrates the interaction 
    between various AI and language processing tools to provide intelligent, context-aware responses 
    to user queries.
    This class integrates large language models with a set of dynamically loaded plugins, 
    enabling the execution of specialized tasks. It manages conversational memory, allowing the 
    engine to maintain context over the course of an interaction. The engine is also capable of 
    processing complex conversational scenarios, making it well-suited for tasks in automated 
    assistance, data analysis, and interactive querying.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the reasoning engine with the provided configuration.

        :param config: Configuration dictionary containing the engine settings.
        """
        super().__init__()
        self.config = LangChainAgentExecutor.Config(**config)
        self.result = LangChainAgentExecutor.Result()
        self.tool_repository = self._init_tool_repository()
        self.engine = {}
        self._init_engine()
        self.executor = self._init_executor()

    def _init_tool_repository(self) -> Optional[ToolRepository]:
        """
        Initialize the tool repository.

        :return: The initialized tool repository or None if initialization failed.
        """
        return ToolRepository.create(self.config.tools)

    def _init_engine(self) -> Dict[str, Any]:
        """
        Initialize the engine components.

        :return: A dictionary containing the initialized engine components.
        """
        logger.debug("Creating Reasoning Engine with Tools")
        self.engine['prompt'] = self._init_prompt(self.config.system_prompt)
        self.engine['tools'] = self._get_tools()
        self.engine['model'] = self._init_model(self.config.model)
        if not self.config.stateless:
            self.engine['memory'] = self._init_memory(self.config.memory)
        self.engine['agent'] = self._init_agent()

    def _init_prompt(self, system_prompt: str) -> ChatPromptTemplate:
        """
        Initialize the prompt with the system prompt.

        :param system_prompt: The system prompt to be used.
        :return: An instance of ChatPromptTemplate initialized with the provided system prompt.
        """
        logger.debug(f"Reasoning Engine system prompt: '{system_prompt}'")
        messages = [("system", system_prompt), ("user", "{input}")]
        if not self.config.stateless:
            messages.insert(1, MessagesPlaceholder(variable_name=self.config.memory["memory_key"]))
        messages.append(MessagesPlaceholder(variable_name="agent_scratchpad"))
        return ChatPromptTemplate.from_messages(messages)

    def _get_tools(self, tool_list: Optional[List[str]] = None) -> Optional[List[StructuredTool]]:
        """
        Retrieve tools from the tool repository.

        :param tool_list: Optional list of tool names to filter the tools.
        :return: A list of tools matching the provided tool names or None if an error occurred.
        """
        result = self.tool_repository.get_tools()
        if result.status == "success":
            tools = [
                tool["object"]
                for tool in result.tools
                if tool_list is None or tool["object"].name in tool_list
            ]
            logger.debug(f"Initialized tools functions {self.config.tools['type']}")
        else:
            tools = None
            logger.error(result.error_message)
        return tools

    def _init_model(self, model_config: Dict[str, Any]) -> Optional[ChatModel]:
        """
        Initialize the chat model.

        :param model_config: Configuration dictionary for the chat model.
        :return: The initialized chat model or None if initialization failed.
        """
        chat_model = ChatModel.create(model_config)
        result = chat_model.get_model()
        if result.status == "success":
            model = result.model
            logger.debug(f"Initialized engine model {model_config['type']}")
        else:
            model = None
            logger.error(result.error_message)
        return model

    def _init_memory(self, memory_config: Dict[str, Any]) -> Optional[ChatMemory]:
        """
        Initialize the chat memory.

        :param memory_config: Configuration dictionary for the chat memory.
        :return: The initialized chat memory or None if initialization failed.
        """
        chat_memory = ChatMemory.create(memory_config)
        result = chat_memory.get_memory()
        if result.status == "success":
            memory = result.memory
            logger.debug(f"Initialized engine memory {memory_config['type']}")
        else:
            memory = None
            logger.error(result.error_message)
        return memory

    def _init_agent(self) -> RunnablePassthrough:
        """
        Initialize the execution agent.

        :return: The initialized Agent
        """
        return create_tool_calling_agent(
            self.engine['model'],
            self.engine['tools'],
            self.engine['prompt'])

    def _init_executor(self) -> AgentExecutor:
        """
        Initialize the agent executor.

        :return: The initialized AgentExecutor.
        """
        kwargs = {
            "agent": self.engine['agent'],
            "tools": self.engine['tools'],
            "verbose": self.config.verbose,
            "handle_parsing_errors": True
        }
        if not self.config.stateless:
            kwargs["memory"] = self.engine['memory']
        return AgentExecutor(**kwargs)


    def run(self, messages: Any) -> 'LangChainAgentExecutor.Result':
        """
        Execute the chain with the input message.

        :param messages: The input messages to process.
        :return: The result of the execution, containing status and completion or error message.
        """
        try:
            self.result.status = "success"
            output = self.executor.invoke({"input": messages})
            self.result.completion = output.get("output", "")
            logger.debug(f"Prompt generated {self.result.completion}")
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while invoking the engine: {e}"
            logger.error(self.result.error_message)
        return self.result


    def clear_memory(self) -> 'LangChainAgentExecutor.Result':
        """
        Clear the conversation history from memory, resetting the conversational context.

        :return: The result of the operation, containing status and completion or error message.
        """
        if not self.config.stateless:
            try:
                self.result.status = "success"
                self.engine['memory'].clear()
                logger.debug("Memory cleared")
            except Exception as e:  # pylint: disable=broad-except
                self.result.status = "failure"
                self.result.error_message = f"An error occurred while clearing the memory: {e}"
                logger.error(self.result.error_message)
        else:
            self.result.status = "success"
            logger.warning("Clear Memory ignoerd: engine is stateless")
        return self.result


    def set_memory(self, memory: Any) -> 'LangChainAgentExecutor.Result':
        """
        Set the engine memory.

        :param memory: The new memory to set for the engine.
        :return: The result of the operation, containing status and completion or error message.
        """
        if not self.config.stateless:
            try:
                self.result.status = "success"
                self.executor.memory = memory
                logger.debug("Changed Engine Memory")
            except Exception as e:  # pylint: disable=broad-except
                self.result.status = "failure"
                self.result.error_message = f"An error occurred while setting the memory: {e}"
                logger.error(self.result.error_message)
        else:
            self.result.status = "success"
            logger.warning("Set Memory ignoerd: engine is stateless")
        return self.result


    def set_tools(self, tool_list: List[str]) -> 'LangChainAgentExecutor.Result':
        """
        Change the tools.

        :param tool_list: List of tool names to set for the engine.
        :return: The result of the operation, containing status and completion or error message.
        """
        try:
            self.result.status = "success"
            self.engine['tools'] = self._get_tools(tool_list)
            self.engine['agent'] = self._init_agent()
            self.executor = self._init_executor()
            logger.debug("Changed Project Tools")
        except Exception as e:  # pylint: disable=broad-except
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while setting the engine tools: {e}"
            logger.error(self.result.error_message)
        return self.result
