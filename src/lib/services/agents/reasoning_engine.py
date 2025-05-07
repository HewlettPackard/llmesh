#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reasoning Engine Module

This module defines the ReasoningEngine class and associated class for 
managing different engines. 
It utilizes the Factory Pattern to allow for flexible extraction methods 
based on the document type.
"""

from typing import Type, Dict, Any
from src.lib.services.agents.reasoning_engines.langchain.agent_executor import (
    LangChainAgentExecutor)
from src.lib.services.agents.reasoning_engines.llamaindex.react import (
    LlamaIndexReActEngine)


class ReasoningEngine:  # pylint: disable=R0903
    """
    A reasoning engine class that uses a factory pattern to return
    the selected reasoning engine
    """

    _engines: Dict[str, Type] = {
        'LangChainAgentExecutor': LangChainAgentExecutor,
        'LlamaIndexReAct': LlamaIndexReActEngine,
    }

    @staticmethod
    def create(config: dict) -> Any:
        """
        Return the appropriate Reasoning Engine based on the provided configuration.

        :param config: Configuration dictionary containing the type of engine.
        :return: An instance of the selected reasoning engine.
        :raises ValueError: If 'type' is not in config or an unsupported type is provided.
        """
        engine_type = config.get('type')
        if not engine_type:
            raise ValueError("Configuration must include 'type'.")
        engine_class = ReasoningEngine._engines.get(engine_type)
        if not engine_class:
            raise ValueError(f"Unsupported extractor type: {engine_type}")
        return engine_class(config)
