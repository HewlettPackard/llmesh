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
from typing import Callable, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP

from src.lib.core.log import Logger
from src.lib.system_services.mcp_auth import TokenVerifier

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

    def __init__(
        self,
        name: str,
        transport: str = "stdio",
        token_verifier: Optional[TokenVerifier] = None,
        auth_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MCP server with transport-specific configuration.

        :param name: Unique server identifier used for logging and identification.
        :type name: str
        :param transport: Transport protocol for client communication.
            Valid options are "stdio", "sse", or "streamable".
        :type transport: str
        :param token_verifier: Optional token verifier for authentication (HTTP transports only)
        :type token_verifier: TokenVerifier, optional
        :param auth_settings: Optional authentication settings dictionary
        :type auth_settings: dict, optional

        Example:
            Create an authenticated streamable HTTP server:

            .. code-block:: python

                from src.lib.system_services.mcp_auth import IntrospectionTokenVerifier

                verifier = IntrospectionTokenVerifier(
                    introspection_endpoint="https://auth.example.com/introspect",
                    server_url="http://localhost:8080"
                )

                server = MCPServer(
                    "api_server",
                    "streamable",
                    token_verifier=verifier,
                    auth_settings={
                        "issuer_url": "https://auth.example.com",
                        "required_scopes": ["mcp:read"],
                        "resource_server_url": "http://localhost:8080"
                    }
                )
        """
        self.name = name
        self.transport = transport
        self.logger = logger
        self.token_verifier = token_verifier
        self._app = None
        self._server_task = None
        self._uvicorn_server = None
        self._running = False

        # Create FastMCP with optional authentication
        if transport in ["sse", "streamable"] and token_verifier:
            # Import auth components
            from mcp.server.auth.settings import AuthSettings as MCPAuthSettings

            # Convert our auth settings to MCP format
            auth_settings_obj = None
            if auth_settings:
                auth_settings_obj = MCPAuthSettings(
                    issuer_url=auth_settings.get("issuer_url"),
                    resource_server_url=auth_settings.get("resource_server_url"),
                    required_scopes=auth_settings.get("required_scopes", [])
                )

            # Pass auth settings as direct keyword argument
            self.mcp = FastMCP(
                name=name,
                auth_server_provider=token_verifier,  # Use token verifier directly
                auth=auth_settings_obj  # Pass directly, not through **settings
            )
            self.logger.info(f"Created authenticated {transport} server '{name}'")
        else:
            # Standard FastMCP without auth
            self.mcp = FastMCP(name=name)
            if transport == "stdio" and token_verifier:
                self.logger.warning("Authentication not supported for stdio transport, ignoring auth settings")

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

        # Shutdown uvicorn server properly
        if self._uvicorn_server:
            self._uvicorn_server.should_exit = True

        if self._server_task:
            # Don't cancel, let uvicorn shutdown gracefully
            try:
                # Wait for uvicorn to shutdown with a timeout
                await asyncio.wait_for(self._server_task, timeout=2.0)
            except asyncio.TimeoutError:
                # If it doesn't shutdown in time, cancel it
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
            except asyncio.CancelledError:
                # Server task was already cancelled
                pass

        self._running = False
        self._app = None
        self._server_task = None
        self._uvicorn_server = None

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

        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def health_check(request):
            return JSONResponse({"status": "healthy", "server": self.name, "transport": self.transport})

        self._app = Starlette(
            routes=[
                Mount("/mcp/", app=self.mcp.sse_app()),
                Route("/health", health_check, methods=["GET"])
            ]
        )

        config = uvicorn.Config(
            app=self._app,
            host=host,
            port=port,
            log_level="warning",
            **kwargs
        )
        self._uvicorn_server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(self._uvicorn_server.serve())

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
        from starlette.applications import Starlette
        from contextlib import asynccontextmanager
        import uvicorn

        # Get the streamable app
        streamable_app = self.mcp.streamable_http_app()

        # For authenticated servers, we need lifecycle management
        if self.token_verifier: # TODO: Need to revisit and create passing integration tests for this, manual testing works partially
            # Access the session manager from the MCP instance
            session_manager = getattr(self.mcp, 'session_manager', None)
            if not session_manager:
                self.logger.error("No session manager found in FastMCP instance")
                raise RuntimeError("FastMCP with auth requires session_manager")

            # Create lifespan context manager
            @asynccontextmanager
            async def lifespan(app: Starlette):
                self.logger.info("Starting Authenticated MCP session manager lifecycle")
                async with session_manager.run():
                    yield
                self.logger.info("Authenticated MCP session manager lifecycle ended")

            # Create a new Starlette app with lifespan
            # Copy routes from the auth app
            routes = list(streamable_app.routes)  # Make a copy

            self._app = Starlette(
                routes=routes,
                lifespan=lifespan,
                debug=False
            )

            # Copy middleware from the auth app
            for mw in streamable_app.user_middleware:
                self._app.add_middleware(mw.cls, **mw.kwargs)

            # Add health check route
            from starlette.routing import Route
            from starlette.responses import JSONResponse

            async def health_check(request):
                return JSONResponse({"status": "healthy", "server": self.name, "transport": self.transport})

            health_route = Route("/health", health_check, methods=["GET"])
            self._app.routes.append(health_route)

        else:
            # For non-authenticated servers, use FastAPI directly
            self._app = FastAPI(
                title=f"MCP Server: {self.name}",
                docs_url="/docs"
            )

            @self._app.get("/health")
            async def health_check():
                return {"status": "healthy", "server": self.name, "transport": self.transport}

            # Mount at /mcp/ for non-authenticated servers
            self._app.mount("/mcp/", streamable_app)
            self.logger.info("Mounted streamable app at /mcp/ for non-authenticated server")

        config = uvicorn.Config(
            app=self._app,
            host=host,
            port=port,
            log_level="warning",
            **kwargs
        )
        self._uvicorn_server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(self._uvicorn_server.serve())

    def __repr__(self):
        """
        Return string representation of the server.

        :return: String representation showing server name, transport, and running status.
        :rtype: str
        """
        return f"MCPServer(name='{self.name}', transport='{self.transport}', running={self._running})"
