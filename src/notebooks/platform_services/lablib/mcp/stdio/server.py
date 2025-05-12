#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP server using stdio (Standard Input/Output) transport.

This script sets up a FastMCP server, registers common tools, resources, and prompts
(defined in a shared 'definitions' module), and then runs the server using
the MCP SDK's default stdio transport. This is suitable for scenarios where
the MCP server is managed as a subprocess by a client.
"""

# mcp_server.py
from mcp.server.fastmcp import FastMCP
from src.notebooks.platform_services.lablib.mcp.definitions import (
    register_tools,
    register_resources,
    register_prompts
)

mcp = FastMCP("ComprehensiveServer")

# Register common components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    print("Starting MCP server...")
    mcp.run()