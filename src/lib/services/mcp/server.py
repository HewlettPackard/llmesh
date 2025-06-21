#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Server Factory

Factory class for creating MCP servers using the official MCP Python SDK.
This module provides a unified interface for exposing platform capabilities
via MCP protocol while integrating with the platform's configuration and service patterns.

Architecture Integration:
- Leverages official MCP SDK (FastMCP) for server implementation
- Follows platform's factory pattern used in other services
- Integrates with existing Config and logging infrastructure
- Provides standardized interfaces for registering tools, resources, and prompts
"""

import asyncio
from typing import Optional, Any, Dict, Union, Callable, List
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from fastapi import FastAPI
import uvicorn

from src.lib.core.log import Logger
from src.lib.core.config import Config as PlatformConfig

logger = Logger().get_logger()


class MCPServer:
    """
    Factory class for creating MCP servers.

    This class follows the platform's established factory pattern and provides
    a unified interface for exposing platform capabilities via MCP protocol
    regardless of transport type.
    """

    class Config(BaseModel):
        """
        Configuration for MCP Server Factory.

        Supports multiple transport types and provides transport-specific
        configuration options while maintaining consistency with platform patterns.
        """
        name: str = Field(
            ...,
            description="Unique name identifier for this MCP server"
        )
        transport: str = Field(
            ...,
            description="Transport type: 'stdio', 'sse', or 'streamable'"
        )

        # HTTP Transport Configuration (SSE and Streamable)
        host: Optional[str] = Field(
            default="localhost",
            description="Host address for HTTP transports"
        )
        port: Optional[int] = Field(
            default=8000,
            description="Port number for HTTP transports"
        )
        mount_path: Optional[str] = Field(
            default="/mcp",
            description="Mount path for HTTP endpoints"
        )
        stateless_http: Optional[bool] = Field(
            default=False,
            description="Enable stateless HTTP mode for streamable transport"
        )

        # General Configuration
        debug: Optional[bool] = Field(
            default=False,
            description="Enable debug logging for this server"
        )
        auto_start: Optional[bool] = Field(
            default=True,
            description="Auto-start server when created (STDIO only)"
        )

    class Result(BaseModel):
        """
        Result of MCP Server operations.

        Standardized result format following platform conventions.
        """
        status: str = Field(
            default="success",
            description="Operation status: 'success', 'error', or 'timeout'"
        )
        data: Optional[Any] = Field(
            default=None,
            description="Operation result data"
        )
        error_message: Optional[str] = Field(
            default=None,
            description="Error description if operation failed"
        )
        error_code: Optional[str] = Field(
            default=None,
            description="Structured error code for programmatic handling"
        )
        server_name: Optional[str] = Field(
            default=None,
            description="Name of the MCP server"
        )

    @staticmethod
    def create(config: Union[Dict, Config, str]) -> 'MCPServerManager':
        """
        Create an MCP server manager based on configuration.

        Args:
            config: Configuration dictionary, Config object, or path to config file

        Returns:
            MCPServerManager instance for managing the server
        """
        # Handle different config input types
        if isinstance(config, str):
            # Assume it's a file path
            platform_config = PlatformConfig(config_file=config)
            mcp_config = platform_config.settings.get('mcp', {})
            server_config = MCPServer.Config(**mcp_config)
        elif isinstance(config, dict):
            server_config = MCPServer.Config(**config)
        else:
            server_config = config

        return MCPServerManager(server_config)

    @staticmethod
    def get_available_transports() -> Dict[str, str]:
        """
        Get available transport types and their descriptions.

        Returns:
            Dictionary mapping transport names to descriptions
        """
        return {
            "stdio": "Standard Input/Output - subprocess-based communication",
            "sse": "Server-Sent Events - HTTP-based streaming communication",
            "streamable": "Streamable HTTP - FastAPI-based HTTP transport with optional streaming"
        }


class MCPServerManager:
    """
    Manager class for handling MCP server lifecycle and capability registration.

    This class wraps the MCP SDK's FastMCP functionality and provides
    platform-consistent interfaces for server management.
    """

    def __init__(self, config: MCPServer.Config):
        """
        Initialize the MCP server manager.

        Args:
            config: MCP server configuration
        """
        self.config = config
        self.name = config.name
        self.transport = config.transport
        self.is_running = False

        # Setup logging with server name
        self.logger = logger
        if config.debug:
            self.logger.setLevel("DEBUG")

        # Create FastMCP instance with appropriate configuration
        if self.transport == "streamable":
            self.mcp = FastMCP(name=self.name, stateless_http=self.config.stateless_http)
        else:
            self.mcp = FastMCP(name=self.name)

        # For SSE transport, we'll need Starlette app
        self._app: Optional[Starlette] = None
        self._server_task: Optional[asyncio.Task] = None

    def register_tool(self,
                     name: Optional[str] = None,
                     description: Optional[str] = None):
        """
        Decorator for registering tools with the MCP server.

        This provides a convenient way to register platform capabilities
        as MCP tools that can be called by clients.

        Args:
            name: Tool name (if None, uses function name)
            description: Tool description

        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            # Use FastMCP's tool decorator
            if description:
                return self.mcp.tool(description=description)(func)
            else:
                return self.mcp.tool()(func)
        return decorator

    def register_resource(self, uri_template: str):
        """
        Decorator for registering resources with the MCP server.

        Args:
            uri_template: URI template for the resource (e.g., "config://{key}")

        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            return self.mcp.resource(uri_template)(func)
        return decorator

    def register_prompt(self, name: str):
        """
        Decorator for registering prompts with the MCP server.

        Args:
            name: Prompt name

        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            return self.mcp.prompt(name)(func)
        return decorator

    def add_platform_tools(self):
        """
        Add common platform tools to the MCP server.

        This method registers standard platform capabilities as MCP tools,
        making them available to MCP clients.
        """
        @self.register_tool(description="Get platform status and health information")
        def get_platform_status() -> Dict[str, Any]:
            """Get current platform status"""
            return {
                "status": "healthy",
                "server_name": self.name,
                "transport": self.transport,
                "capabilities": ["tools", "resources", "prompts"]
            }

        @self.register_tool(description="Echo input text for testing connectivity")
        def echo(text: str) -> str:
            """Echo the input text"""
            return f"Echo: {text}"

        self.logger.info("Added platform tools to MCP server")

    def add_platform_resources(self):
        """
        Add common platform resources to the MCP server.

        This method exposes platform configuration and status as MCP resources.
        """
        @self.register_resource("platform://config")
        def platform_config():
            """Platform configuration resource"""
            return {
                "server_name": self.name,
                "transport": self.transport,
                "debug": self.config.debug
            }

        @self.register_resource("platform://status")
        def platform_status():
            """Platform status resource"""
            return {
                "running": self.is_running,
                "server_name": self.name,
                "transport": self.transport
            }

        self.logger.info("Added platform resources to MCP server")

    def add_platform_prompts(self):
        """
        Add common platform prompts to the MCP server.
        """
        @self.register_prompt("system_info")
        def system_info_prompt(context: str = "general"):
            """System information prompt template"""
            return [
                f"You are an assistant for the {self.name} MCP server.",
                f"Context: {context}",
                f"Transport: {self.transport}",
                "Please provide helpful information about the platform."
            ]

        self.logger.info("Added platform prompts to MCP server")

    async def start(self) -> MCPServer.Result:
        """
        Start the MCP server.

        Returns:
            Result object indicating success or failure
        """
        try:
            if self.is_running:
                return MCPServer.Result(
                    status="error",
                    error_message="Server is already running",
                    error_code="ALREADY_RUNNING",
                    server_name=self.name
                )

            self.logger.info(f"Starting MCP server '{self.name}' with {self.transport} transport")

            if self.transport == "stdio":
                await self._start_stdio()
            elif self.transport == "sse":
                await self._start_sse()
            elif self.transport == "streamable":
                await self._start_streamable()
            else:
                raise ValueError(f"Unsupported transport type: {self.transport}")

            self.is_running = True
            self.logger.info(f"MCP server '{self.name}' started successfully")

            return MCPServer.Result(
                status="success",
                data={
                    "server_name": self.name,
                    "transport": self.transport,
                    "running": True
                },
                server_name=self.name
            )

        except Exception as e:
            self.logger.error(f"Failed to start server '{self.name}': {str(e)}")
            return MCPServer.Result(
                status="error",
                error_message=f"Failed to start server: {str(e)}",
                error_code="START_FAILED",
                server_name=self.name
            )

    async def _start_stdio(self):
        """Start server with STDIO transport."""
        # For STDIO, we typically run the server directly
        # This would be called when the server is launched as a subprocess
        if self.config.auto_start:
            # Run the server using MCP's built-in STDIO support
            self.mcp.run()
        else:
            self.logger.info("STDIO server configured but auto_start disabled")

    async def _start_sse(self):
        """Start server with SSE transport."""
        # Create Starlette app with MCP SSE endpoint
        self._app = Starlette(
            routes=[
                Mount(self.config.mount_path, app=self.mcp.sse_app(self.config.mount_path)),
            ]
        )

        # Start the server in a background task
        self._server_task = asyncio.create_task(
           self._run_sse_server()
        )

    async def _start_streamable(self):
        """Start server with Streamable HTTP transport."""
        self.logger.info("Starting MCP server with Streamable HTTP transport")
        # Create FastAPI app with MCP streamable HTTP endpoint
        self._app = FastAPI(
            title=f"MCP Server: {self.name}",
            description=f"Model Context Protocol server with streamable HTTP transport"
        )

        # Mount the MCP streamable HTTP app
        self._app.mount(self.config.mount_path, self.mcp.streamable_http_app())

        # Start the server in a background task
        self._server_task = asyncio.create_task(
            self._run_streamable_server()
        )

    async def _run_sse_server(self):
        """Run the SSE server with Uvicorn."""
        config = uvicorn.Config(
            app=self._app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if self.config.debug else "warning"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def _run_streamable_server(self):
        """Run the Streamable HTTP server with Uvicorn."""
        config = uvicorn.Config(
            app=self._app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if self.config.debug else "warning"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def stop(self) -> MCPServer.Result:
        """
        Stop the MCP server.

        Returns:
            Result object indicating success or failure
        """
        try:
            if not self.is_running:
                return MCPServer.Result(
                    status="error",
                    error_message="Server is not running",
                    error_code="NOT_RUNNING",
                    server_name=self.name
                )

            self.logger.info(f"Stopping MCP server '{self.name}'")

            if self._server_task:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass

            self.is_running = False
            self.logger.info(f"MCP server '{self.name}' stopped successfully")

            return MCPServer.Result(
                status="success",
                data={
                    "server_name": self.name,
                    "running": False
                },
                server_name=self.name
            )

        except Exception as e:
            self.logger.error(f"Failed to stop server '{self.name}': {str(e)}")
            return MCPServer.Result(
                status="error",
                error_message=f"Failed to stop server: {str(e)}",
                error_code="STOP_FAILED",
                server_name=self.name
            )

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information and statistics.

        Returns:
            Dictionary with server information
        """
        return {
            "name": self.name,
            "transport": self.transport,
            "running": self.is_running,
            "config": {
                "host": getattr(self.config, 'host', None),
                "port": getattr(self.config, 'port', None),
                "mount_path": getattr(self.config, 'mount_path', None),
                "debug": self.config.debug
            }
        }

    def __repr__(self) -> str:
        """String representation of the server manager."""
        return f"MCPServerManager(name='{self.name}', transport='{self.transport}', running={self.is_running})"