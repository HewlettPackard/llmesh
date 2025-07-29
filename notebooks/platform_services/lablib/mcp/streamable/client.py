#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of an MCP client connecting via Streamable HTTP transport.

This script demonstrates how to connect to an MCP server that exposes a streamable HTTP endpoint.
It uses the `streamablehttp_client` from the MCP SDK to establish a connection and then
runs a common demonstration sequence (`run_demo` from `client_util`) to interact
with the server's tools, resources, and prompts.
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from notebooks.platform_services.lablib.mcp.client_util import run_demo

async def main():
    server_url = "http://localhost:8000/math/mcp"
    print(f"Connecting to Streamable HTTP server at {server_url}...")

    # Connect to the Streamable HTTP server
    async with streamablehttp_client(server_url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await run_demo(session)

if __name__ == "__main__":
    asyncio.run(main())