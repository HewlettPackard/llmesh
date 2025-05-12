#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP client connecting via stdio (Standard Input/Output).

This script demonstrates how to launch and connect to an MCP server as a subprocess,
communicating with it over stdio. It uses the `stdio_client` from the MCP SDK
to manage the server process and establish a connection. Once connected, it
runs a common demonstration sequence (`run_demo` from `client_util`) to interact
with the server's tools, resources, and prompts.
"""

# mcp_client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.notebooks.platform_services.lablib.mcp.client_util import run_demo

async def main():
    import os
    file_dir = os.path.dirname(__file__)
    server_params = StdioServerParameters(
        command="uv",
        args=["run", os.path.join(file_dir, "server.py")]
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await run_demo(session)

if __name__ == "__main__":
    asyncio.run(main())
