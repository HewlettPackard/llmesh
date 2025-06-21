#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Platform Adapters

This module provides adapters for integrating MCP capabilities with existing
platform services including LangChain tools, reasoning engines, and memory systems.
"""

from .langchain_tools import MCPToLangChainAdapter

__all__ = [
    'MCPToLangChainAdapter'
]