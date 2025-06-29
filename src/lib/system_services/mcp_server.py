#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Server

Simple wrapper around FastMCP for creating MCP servers.
Supports stdio, sse, and streamable transports.
"""

import asyncio
from typing import Callable, Optional, Any

from mcp.server.fastmcp import FastMCP
from src.lib.core.log import Logger

logger = Logger().get_logger()


class MCPServer:
    """
    Simple wrapper around FastMCP for creating MCP servers.
    """

    def __init__(self, name: str, transport: str = "stdio"):
        """
        Initialize MCP server.

        Args:
            name: Server name
            transport: Transport type (stdio, sse, streamable)
        """
        self.name = name
        self.transport = transport
        self.mcp = FastMCP(name=name)
        self.logger = logger
        self._app = None
        self._server_task = None
        self._running = False

    # Delegation to FastMCP decorators
    def tool(self, description: str = None):
        """Decorator to register a tool."""
        return self.mcp.tool(description=description)

    def resource(self, uri_template: str):
        """Decorator to register a resource."""
        return self.mcp.resource(uri_template)

    def prompt(self, name: str):
        """Decorator to register a prompt."""
        return self.mcp.prompt(name)

    def register_tool(self, name: str, handler: Callable, description: str = None):
        """
        Register a tool programmatically.

        Args:
            name: Tool name
            handler: Tool handler function
            description: Tool description

        Returns:
            The wrapped handler
        """
        # Create wrapper that works with FastMCP
        if asyncio.iscoroutinefunction(handler):
            @self.mcp.tool(description=description)
            async def tool_wrapper(**kwargs):
                return await handler(**kwargs)
        else:
            @self.mcp.tool(description=description)
            def tool_wrapper(**kwargs):
                return handler(**kwargs)

        # Store with the provided name
        tool_wrapper.__name__ = name
        return tool_wrapper

    async def start(self, host: str = "localhost", port: int = 8000, **kwargs):
        """
        Start the server based on transport type.

        Args:
            host: Host address (for HTTP transports)
            port: Port number (for HTTP transports)
            **kwargs: Additional server options
        """
        if self._running:
            self.logger.warning(f"Server '{self.name}' is already running")
            return

        try:
            if self.transport == "stdio":
                # For stdio, this is typically called by the spawning process
                self.logger.info(f"Starting stdio server '{self.name}'")
                self.mcp.run()

            elif self.transport == "sse":
                self.logger.info(f"Starting SSE server '{self.name}' on {host}:{port}")
                await self._start_sse_server(host, port, **kwargs)

            elif self.transport == "streamable":
                self.logger.info(f"Starting streamable server '{self.name}' on {host}:{port}")
                await self._start_streamable_server(host, port, **kwargs)

            else:
                raise ValueError(f"Unknown transport: {self.transport}")

            self._running = True

        except Exception as e:
            self.logger.error(f"Failed to start server '{self.name}': {e}")
            raise

    async def stop(self):
        """Stop the server if running."""
        if not self._running:
            return

        self.logger.info(f"Stopping server '{self.name}'")

        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass

        self._running = False
        self._app = None
        self._server_task = None

    async def _start_sse_server(self, host: str, port: int, **kwargs):
        """Start SSE HTTP server."""
        from starlette.applications import Starlette
        from starlette.routing import Mount
        import uvicorn

        self._app = Starlette(
            routes=[Mount("/mcp", app=self.mcp.sse_app())]
        )

        config = uvicorn.Config(
            app=self._app,
            host=host,
            port=port,
            log_level="warning",
            **kwargs
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())

    async def _start_streamable_server(self, host: str, port: int, **kwargs):
        """Start streamable HTTP server."""
        from fastapi import FastAPI
        import uvicorn

        self._app = FastAPI(
            title=f"MCP Server: {self.name}",
            docs_url="/docs"
        )
        self._app.mount("/mcp", self.mcp.streamable_http_app())

        config = uvicorn.Config(
            app=self._app,
            host=host,
            port=port,
            log_level="warning",
            **kwargs
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())

    def __repr__(self):
        return f"MCPServer(name='{self.name}', transport='{self.transport}', running={self._running})"
