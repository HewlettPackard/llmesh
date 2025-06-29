#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Server module for creating Model Context Protocol servers.

This module provides the MCPServer class, a simplified wrapper around FastMCP
that enables creation of MCP servers supporting various transport protocols
including stdio, sse, and streamable HTTP transports. The server acts as a
bridge between the platform's internal services and external MCP clients.

Example:
    Basic server creation and tool registration:

    .. code-block:: python

        from src.lib.system_services.mcp_server import MCPServer

        # Create server
        server = MCPServer("my_service", "streamable")

        # Register tools using decorators
        @server.tool(description="Add two numbers")
        def add_numbers(a: int, b: int) -> int:
            return a + b

        # Start the server
        await server.start(host="localhost", port=8080)
"""

import asyncio
from typing import Callable, Optional, Any

from mcp.server.fastmcp import FastMCP
from src.lib.core.log import Logger

logger = Logger().get_logger()


class MCPServer:
    """
    Server for creating Model Context Protocol (MCP) servers within LATMesh.

    This class provides a simplified interface for creating MCP servers using
    various transport protocols. It wraps FastMCP functionality and handles
    server lifecycle management, tool registration, and transport-specific
    server startup.

    Attributes:
        name (str): The server name used for identification and logging.
        transport (str): The transport protocol ("stdio", "sse", or "streamable").
        mcp: The underlying FastMCP instance for MCP functionality.
        logger: Logger instance for debugging and error reporting.
    """

    def __init__(self, name: str, transport: str = "stdio"):
        """
        Initialize MCP server with transport-specific configuration.

        :param name: Unique server identifier used for logging and identification.
        :type name: str
        :param transport: Transport protocol for client communication.
            Valid options are "stdio", "sse", or "streamable".
        :type transport: str

        Example:
            Create a streamable HTTP server:

            .. code-block:: python

                server = MCPServer("api_server", "streamable")
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
        """
        Decorator to register a tool with the MCP server.

        :param description: Optional description of the tool's functionality.
        :type description: str, optional
        :return: Decorator function for tool registration.
        :rtype: Callable

        Example:
            .. code-block:: python

                @server.tool(description="Calculate the sum of two numbers")
                def add(a: int, b: int) -> int:
                    return a + b
        """
        return self.mcp.tool(description=description)

    def resource(self, uri_template: str):
        """
        Decorator to register a resource with the MCP server.

        :param uri_template: URI template pattern for the resource.
        :type uri_template: str
        :return: Decorator function for resource registration.
        :rtype: Callable

        Example:
            .. code-block:: python

                @server.resource("config://settings")
                def get_settings():
                    return {"theme": "dark", "language": "en"}
        """
        return self.mcp.resource(uri_template)

    def prompt(self, name: str):
        """
        Decorator to register a prompt template with the MCP server.

        :param name: Name of the prompt template.
        :type name: str
        :return: Decorator function for prompt registration.
        :rtype: Callable

        Example:
            .. code-block:: python

                @server.prompt("analysis")
                def analysis_prompt(data: str):
                    return f"Analyze the following data: {data}"
        """
        return self.mcp.prompt(name)

    def register_tool(self, name: str, handler: Callable, description: str = None):
        """
        Register a tool programmatically without using decorators.

        This method allows registration of existing functions or methods as MCP tools,
        supporting both synchronous and asynchronous handlers.

        :param name: Name to assign to the tool in the MCP server.
        :type name: str
        :param handler: Function or method to handle tool invocations.
        :type handler: Callable
        :param description: Optional description of the tool's functionality.
        :type description: str, optional
        :return: The wrapped handler function with MCP registration applied.
        :rtype: Callable

        Example:
            Register an existing service method:

            .. code-block:: python

                def multiply(x: int, y: int) -> int:
                    return x * y

                server.register_tool("multiply_numbers", multiply, "Multiply two integers")
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
        Start the MCP server based on the configured transport type.

        This method initializes and starts the server using the appropriate transport
        protocol. For stdio transport, it runs the server directly. For HTTP-based
        transports (sse, streamable), it starts an HTTP server on the specified host and port.

        :param host: Host address to bind the server to (for HTTP transports only).
        :type host: str
        :param port: Port number to bind the server to (for HTTP transports only).
        :type port: int
        :param kwargs: Additional server configuration options passed to the underlying server.
        :type kwargs: dict

        :raises ValueError: If an unsupported transport type is specified.
        :raises Exception: If server startup fails.

        Example:
            Start an SSE server:

            .. code-block:: python

                await server.start(host="0.0.0.0", port=8080)
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
        """
        Stop the MCP server if it is currently running.

        This method gracefully shuts down the server, cancelling any running tasks
        and cleaning up resources. It's safe to call this method multiple times.
        """
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
        """
        Start Server-Sent Events (SSE) HTTP server.

        Creates a Starlette application with SSE transport for MCP communication
        and starts it using uvicorn.

        :param host: Host address to bind the server to.
        :type host: str
        :param port: Port number to bind the server to.
        :type port: int
        :param kwargs: Additional uvicorn server configuration options.
        :type kwargs: dict
        """
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
        """
        Start streamable HTTP server for full bidirectional MCP communication.

        Creates a FastAPI application with streamable HTTP transport for MCP
        communication and starts it using uvicorn. This transport supports
        full bidirectional streaming communication over HTTP.

        :param host: Host address to bind the server to.
        :type host: str
        :param port: Port number to bind the server to.
        :type port: int
        :param kwargs: Additional uvicorn server configuration options.
        :type kwargs: dict
        """
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
        """
        Return string representation of the server.

        :return: String representation showing server name, transport, and running status.
        :rtype: str
        """
        return f"MCPServer(name='{self.name}', transport='{self.transport}', running={self._running})"
