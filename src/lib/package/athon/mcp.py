#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module re-exports key functionalities related to MCP (Model Context Protocol) interface.
Provides comprehensive MCP client and server functionality for the LATMesh platform.
It implements the Model Context Protocol specification to enable seamless integration
with internal/external tools and services.

Architecture Overview:
- Clients: Connect to external MCP servers via various transports
- Servers: Expose platform capabilities as MCP servers
- Registry: Capability discovery and caching system
- Adapters: Integration with existing platform services

Transport Support:
- STDIO: Local process communication (high performance, secure)
- SSE: Server-Sent Events for HTTP-based services
- WebSocket: Real-time bidirectional communication
"""

from src.lib.services.mcp.client import MCPClient
from src.lib.services.mcp.server import MCPServer
from src.lib.services.mcp.registry import MCPRegistry

__all__ = [
    'MCPClient',
    'MCPServer',
    'MCPRegistry'
]

__version__ = '0.1.0'
__author__ = 'LLM Agentic Tool Mesh Team'
