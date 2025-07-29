#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP server using streamable HTTP transport with FastAPI.

This script demonstrates how to set up a FastMCP server with stateless HTTP enabled,
register tools, resources, and prompts, and serve them over a streamable HTTP endpoint
integrated with a FastAPI application. It shows how to run the server using Uvicorn.
The definitions for tools, resources, and prompts are included directly in this file
for a self-contained example.
"""

from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
from notebooks.platform_services.lablib.mcp.definitions import (
    register_tools,
    register_resources,
    register_prompts
)

mcp = FastMCP(name="MathServer", stateless_http=True)

# Tool specific to this server example
@mcp.tool(description="A simple add tool")
def add_two() -> str:
    return  "2 + 2 = 4"

# Register common components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

# Create FastAPI app with MCP's lifespan
app = FastAPI(lifespan=lambda app: mcp.session_manager.run())
app.mount("/math", mcp.streamable_http_app())

if __name__ == "__main__":
    # Explicitly run with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)