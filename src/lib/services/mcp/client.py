#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Client Factory

Factory class for creating MCP client connections using the official MCP Python SDK.
This module provides a unified interface for connecting to MCP servers via different
transports while integrating with the platform's configuration and logging systems.

Architecture Integration:
- Leverages official MCP SDK (mcp package) for protocol implementation
- Follows platform's factory pattern used in chat, rag, and agents services
- Integrates with existing Config and logging infrastructure
- Provides standardized Result objects for consistent error handling
"""

from contextlib import asynccontextmanager
from typing import Optional, Any, Dict, Union, AsyncGenerator
from pydantic import BaseModel, Field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from src.lib.core.log import Logger
from src.lib.core.config import Config as PlatformConfig

logger = Logger().get_logger()


class MCPClient:
    """
    Factory class for creating MCP client connections.

    This class follows the platform's established factory pattern and provides
    a unified interface for connecting to MCP servers regardless of transport type.
    It integrates with the existing configuration system and provides consistent
    error handling through Result objects.
    """

    class Config(BaseModel):
        """
        Configuration for MCP Client Factory.

        Supports multiple transport types and provides transport-specific
        configuration options while maintaining consistency with platform patterns.
        """
        name: str = Field(
            ...,
            description="Unique name identifier for this MCP client configuration"
        )
        transport: str = Field(
            ...,
            description="Transport type: 'stdio', 'sse', or 'streamable'"
        )

        # STDIO Transport Configuration
        command: Optional[str] = Field(
            default=None,
            description="Command to execute for STDIO transport (e.g., 'python', 'uv')"
        )
        args: Optional[list] = Field(
            default=None,
            description="Arguments for STDIO command (e.g., ['run', 'server.py'])"
        )
        cwd: Optional[str] = Field(
            default=None,
            description="Working directory for STDIO server process"
        )
        env: Optional[Dict[str, str]] = Field(
            default=None,
            description="Environment variables for STDIO server process"
        )

        # HTTP Transport Configuration (SSE and Streamable)
        url: Optional[str] = Field(
            default=None,
            description="HTTP endpoint URL (e.g., 'http://localhost:8000/server/sse' or 'http://localhost:8000/mcp')"
        )
        headers: Optional[Dict[str, str]] = Field(
            default=None,
            description="HTTP headers for streamable transport"
        )

        # General Configuration
        timeout: Optional[int] = Field(
            default=30,
            description="Connection timeout in seconds"
        )
        debug: Optional[bool] = Field(
            default=False,
            description="Enable debug logging for this client"
        )

    class Result(BaseModel):
        """
        Result of MCP Client operations.

        Standardized result format following platform conventions,
        providing consistent error handling and response structure.
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
        client_name: Optional[str] = Field(
            default=None,
            description="Name of the MCP client configuration"
        )

    @staticmethod
    def create(config: Union[Dict, Config, str]) -> 'MCPClientManager':
        """
        Create an MCP client manager based on configuration.

        Args:
            config: Configuration dictionary, Config object, or path to config file

        Returns:
            MCPClientManager instance for managing the connection
        """
        # Handle different config input types
        if isinstance(config, str):
            # Assume it's a file path
            platform_config = PlatformConfig(config_file=config)
            mcp_config = platform_config.settings.get('mcp', {})
            client_config = MCPClient.Config(**mcp_config)
        elif isinstance(config, dict):
            client_config = MCPClient.Config(**config)
        else:
            client_config = config

        return MCPClientManager(client_config)

    @staticmethod
    def get_available_transports() -> Dict[str, str]:
        """
        Get available transport types and their descriptions.

        Returns:
            Dictionary mapping transport names to descriptions
        """
        return {
            "stdio": "Standard Input/Output - subprocess communication",
            "sse": "Server-Sent Events - HTTP-based streaming communication",
            "streamable": "Streamable HTTP - HTTP-based request/response communication"
        }


class MCPClientManager:
    """
    Manager class for handling MCP client connections and operations.

    This class wraps the MCP SDK's client functionality and provides
    platform-consistent interfaces for connection management and operations.
    """

    def __init__(self, config: MCPClient.Config):
        """
        Initialize the MCP client manager.

        Args:
            config: MCP client configuration
        """
        self.config = config
        self.name = config.name
        self.transport = config.transport

        # Setup logging with client name
        self.logger = logger
        if config.debug:
            self.logger.setLevel("DEBUG")

        self._session: Optional[ClientSession] = None
        self._connection_context = None

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[ClientSession, None]:
        """
        Establish connection to MCP server and return session.

        This is an async context manager that handles connection lifecycle,
        ensuring proper cleanup when the connection is no longer needed.

        Yields:
            ClientSession for interacting with the MCP server

        Raises:
            ValueError: If transport type is unsupported or configuration is invalid
            ConnectionError: If connection fails
        """
        try:
            self.logger.info(f"Connecting to MCP server '{self.name}' via {self.transport}")

            if self.transport == "stdio":
                await self._connect_stdio()
            elif self.transport == "sse":
                await self._connect_sse()
            elif self.transport == "streamable":
                await self._connect_streamable()
            else:
                raise ValueError(f"Unsupported transport type: {self.transport}")

            if self._session is None:
                raise ConnectionError(f"Failed to establish session for '{self.name}'")

            self.logger.info(f"Successfully connected to MCP server '{self.name}'")
            yield self._session

        except Exception as e:
            self.logger.error(f"Connection failed for '{self.name}': {str(e)}")
            raise
        finally:
            await self._cleanup_connection()

    async def _connect_stdio(self) -> None:
        """Setup STDIO connection using MCP SDK."""
        if not self.config.command:
            raise ValueError("STDIO transport requires 'command' configuration")

        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args or [],
            cwd=self.config.cwd,
            env=self.config.env
        )

        self.logger.debug(f"Starting STDIO server: {self.config.command} {' '.join(self.config.args or [])}")

        # Store connection context for cleanup
        self._connection_context = stdio_client(server_params)
        reader, writer = await self._connection_context.__aenter__()

        # Create session
        session_context = ClientSession(reader, writer)
        self._session = await session_context.__aenter__()

        # Store session context for cleanup
        self._session_context = session_context

    async def _connect_sse(self) -> None:
        """Setup SSE connection using MCP SDK."""
        if not self.config.url:
            raise ValueError("SSE transport requires 'url' configuration")

        self.logger.debug(f"Connecting to SSE endpoint: {self.config.url}")

        # Store connection context for cleanup
        self._connection_context = sse_client(url=self.config.url)
        reader, writer = await self._connection_context.__aenter__()

        # Create session
        session_context = ClientSession(reader, writer)
        self._session = await session_context.__aenter__()

        # Store session context for cleanup
        self._session_context = session_context

    async def _connect_streamable(self) -> None:
        """Setup Streamable HTTP connection using MCP SDK."""
        if not self.config.url:
            raise ValueError("Streamable transport requires 'url' configuration")

        self.logger.debug(f"Connecting to Streamable HTTP endpoint: {self.config.url}")

        # Use official MCP SDK streamable HTTP client with proper timeout configuration
        import datetime
        timeout_seconds = self.config.timeout or 30

        try:
            self._connection_context = streamablehttp_client(
                url=self.config.url,
                headers=self.config.headers or {},
                timeout=datetime.timedelta(seconds=timeout_seconds),
                sse_read_timeout=datetime.timedelta(seconds=timeout_seconds * 2)  # Give more time for SSE reads
            )
            reader, writer, _ = await self._connection_context.__aenter__()

            # Create session with longer read timeout for initialization
            session_context = ClientSession(
                reader,
                writer,
                read_timeout_seconds=datetime.timedelta(seconds=timeout_seconds)
            )
            self._session = await session_context.__aenter__()

            # Store session context for cleanup
            self._session_context = session_context

        except Exception as e:
            self.logger.error(f"Failed to connect to streamable endpoint: {e}")
            raise

    async def _cleanup_connection(self) -> None:
        """Clean up connection resources."""
        try:
            if hasattr(self, '_session_context') and self._session_context:
                await self._session_context.__aexit__(None, None, None)

            if self._connection_context:
                await self._connection_context.__aexit__(None, None, None)

            self.logger.debug(f"Cleaned up connection for '{self.name}'")
        except Exception as e:
            self.logger.warning(f"Error during cleanup for '{self.name}': {str(e)}")
        finally:
            self._session = None
            self._connection_context = None

    async def test_connection(self) -> MCPClient.Result:
        """
        Test the connection to the MCP server.

        Returns:
            Result object indicating connection success or failure
        """
        try:
            async with self.connect() as session:
                # Initialize the session to verify connection
                await session.initialize()

                # Try to list tools as a basic connectivity test
                tools = await session.list_tools()

                return MCPClient.Result(
                    status="success",
                    data={
                        "connected": True,
                        "tool_count": len(tools.tools),
                        "transport": self.transport
                    },
                    client_name=self.name
                )

        except Exception as e:
            self.logger.error(f"Connection test failed for '{self.name}': {str(e)}")
            return MCPClient.Result(
                status="error",
                error_message=f"Connection test failed: {str(e)}",
                error_code="CONNECTION_TEST_FAILED",
                client_name=self.name
            )

    async def get_capabilities(self) -> MCPClient.Result:
        """
        Get server capabilities (tools, resources, prompts).

        Returns:
            Result object with server capabilities
        """
        try:
            async with self.connect() as session:
                await session.initialize()

                # Gather all capabilities
                tools_result = await session.list_tools()
                resources_result = await session.list_resources()
                prompts_result = await session.list_prompts()

                capabilities = {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": getattr(tool, 'description', ''),
                            "inputSchema": getattr(tool, 'inputSchema', {})
                        }
                        for tool in tools_result.tools
                    ],
                    "resources": [
                        {
                            "uri": str(resource.uri),
                            "name": getattr(resource, 'name', ''),
                            "description": getattr(resource, 'description', ''),
                            "mimeType": getattr(resource, 'mimeType', 'text/plain')
                        }
                        for resource in resources_result.resources
                    ],
                    "prompts": [
                        {
                            "name": prompt.name,
                            "description": getattr(prompt, 'description', ''),
                            "arguments": getattr(prompt, 'arguments', [])
                        }
                        for prompt in prompts_result.prompts
                    ]
                }

                return MCPClient.Result(
                    status="success",
                    data=capabilities,
                    client_name=self.name
                )

        except Exception as e:
            self.logger.error(f"Failed to get capabilities for '{self.name}': {str(e)}")
            return MCPClient.Result(
                status="error",
                error_message=f"Failed to get capabilities: {str(e)}",
                error_code="CAPABILITY_DISCOVERY_FAILED",
                client_name=self.name
            )

    def __repr__(self) -> str:
        """String representation of the client manager."""
        return f"MCPClientManager(name='{self.name}', transport='{self.transport}')"
