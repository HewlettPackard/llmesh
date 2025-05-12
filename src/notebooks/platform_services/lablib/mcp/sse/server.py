#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP server using SSE (Server-Sent Events) transport.

This script demonstrates how to set up a FastMCP server, register tools,
resources, and prompts, and serve them over an SSE endpoint using Starlette.
It shows two methods for running the server: directly with Uvicorn or using
the MCP SDK's built-in run command.
"""

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn
from src.notebooks.platform_services.lablib.mcp.definitions import (
    register_tools,
    register_resources,
    register_prompts
)

# Create MCP server instance
mcp = FastMCP(name="MathServer")

# Register common components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

# Tool specific to this SSE server
@mcp.tool(description="A simple add tool")
def add_two() -> str:
    return "2 + 2 = 4"

# Method 1: Create Starlette app with MCP's SSE transport
app = Starlette(
    routes=[
        Mount("/math", app=mcp.sse_app("/math")),
    ]
)

# Run with Uvicorn when executed directly
if __name__ == "__main__":
    # Method 1: Run with Starlette/Uvicorn (uncomment to use)
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # Method 2: Run directly with MCP SDK (uncomment to use instead of the above)
    # mcp.run(transport="sse", mount_path="/math")
