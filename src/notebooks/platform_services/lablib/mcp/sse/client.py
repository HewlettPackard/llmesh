#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP client connecting via SSE (Server-Sent Events).

This script demonstrates how to connect to an MCP server that exposes an SSE endpoint.
It uses the `sse_client` from the MCP SDK to establish a connection and then
runs a common demonstration sequence (`run_demo` from `client_util`) to interact
with the server's tools, resources, and prompts.
"""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from src.notebooks.platform_services.lablib.mcp.client_util import run_demo

async def main():
    server_url = "http://localhost:8000/math/sse"
    print(f"Connecting to SSE server at {server_url}...")

    # Connect to the SSE server
    async with sse_client(url=server_url) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await run_demo(session)

if __name__ == "__main__":
    asyncio.run(main())
