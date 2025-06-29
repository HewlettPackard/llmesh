#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Client

Simple wrapper around MCP SDK for connecting to MCP servers within LATMesh.
Supports stdio, sse, and streamable transports.
"""

from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

import datetime
from src.lib.core.log import Logger

logger = Logger().get_logger()


class MCPClient:
    """
    Simple wrapper around MCP SDK for client connections.
    """

    def __init__(self, name: str, transport: str, **connection_params):
        """
        Initialize client with connection parameters.

        Args:
            name: Client name (for logging)
            transport: Transport type (stdio, sse, streamable)
            **connection_params: Transport-specific parameters
                stdio: command, args, env, cwd
                sse/streamable: url, headers, timeout
        """
        self.name = name
        self.transport = transport
        self.connection_params = connection_params
        self.logger = logger
        self._session: Optional[ClientSession] = None
        self._context = None
        self._session_context = None

    async def connect(self):
        """Establish connection to MCP server."""
        if self._session:
            return  # Already connected

        try:
            self.logger.debug(f"Connecting to server '{self.name}' via {self.transport}")

            if self.transport == "stdio":
                await self._connect_stdio()
            elif self.transport == "sse":
                await self._connect_sse()
            elif self.transport == "streamable":
                await self._connect_streamable()
            else:
                raise ValueError(f"Unknown transport: {self.transport}")

            self.logger.info(f"Connected to server '{self.name}'")

        except Exception as e:
            self.logger.error(f"Failed to connect to '{self.name}': {e}")
            raise

    async def disconnect(self):
        """Close the connection."""
        if not self._session:
            return

        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._context:
                await self._context.__aexit__(None, None, None)

            self._session = None
            self._context = None
            self._session_context = None

            self.logger.debug(f"Disconnected from server '{self.name}'")

        except Exception as e:
            self.logger.warning(f"Error during disconnect from '{self.name}': {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the server."""
        await self.connect()

        result = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "inputSchema": getattr(tool, "inputSchema", {})
            }
            for tool in result.tools
        ]

    async def invoke_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Invoke a tool on the server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        await self.connect()

        result = await self._session.call_tool(name, arguments or {})
        return result.content

    async def list_resources(self) -> List[Dict[str, Any]]:
        """Get available resources from the server."""
        await self.connect()

        result = await self._session.list_resources()
        return [
            {
                "uri": str(resource.uri),
                "name": getattr(resource, "name", ""),
                "description": getattr(resource, "description", ""),
                "mimeType": getattr(resource, "mimeType", "text/plain")
            }
            for resource in result.resources
        ]

    async def read_resource(self, uri: str) -> Any:
        """
        Read a resource by URI.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        await self.connect()

        result = await self._session.read_resource(uri)
        return result.content

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """Get available prompts from the server."""
        await self.connect()

        result = await self._session.list_prompts()
        return [
            {
                "name": prompt.name,
                "description": getattr(prompt, "description", ""),
                "arguments": getattr(prompt, "arguments", [])
            }
            for prompt in result.prompts
        ]

    async def _connect_stdio(self):
        """Connect via stdio transport."""
        params = StdioServerParameters(
            command=self.connection_params["command"],
            args=self.connection_params.get("args", []),
            env=self.connection_params.get("env"),
            cwd=self.connection_params.get("cwd")
        )

        self._context = stdio_client(params)
        reader, writer = await self._context.__aenter__()

        self._session_context = ClientSession(reader, writer)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

    async def _connect_sse(self):
        """Connect via SSE transport."""
        self._context = sse_client(url=self.connection_params["url"])
        reader, writer = await self._context.__aenter__()

        self._session_context = ClientSession(reader, writer)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

    async def _connect_streamable(self):
        """Connect via streamable HTTP transport."""
        timeout = datetime.timedelta(
            seconds=self.connection_params.get("timeout", 30)
        )

        self._context = streamablehttp_client(
            url=self.connection_params["url"],
            headers=self.connection_params.get("headers", {}),
            timeout=timeout
        )
        reader, writer, _ = await self._context.__aenter__()

        self._session_context = ClientSession(reader, writer)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()

    def __repr__(self):
        return f"MCPClient(name='{self.name}', transport='{self.transport}', connected={self._session is not None})"
