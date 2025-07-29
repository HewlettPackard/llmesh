#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Platform MCP Registry Singleton

This module provides a singleton registry for managing all MCP servers and clients
across the LLMesh platform. It centralizes the registration, discovery, and
management of platform tools using the Model Context Protocol.

This version uses the new simplified MCP architecture with ephemeral connections.
"""

import os
from typing import Dict, Any, Callable, Optional, List

from src.lib.services.mcp.mcp_directory import MCPDirectory, ServerConfig
from src.lib.services.mcp.client_executor import ClientExecutor
from src.lib.services.mcp.server_host import ServerHost
from src.lib.services.core.log import Logger
from src.lib.services.core.config import Config


# Load configuration
PATH = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(PATH, 'config.yaml')
config = Config(config_path).get_settings()

logger = Logger().configure(config['logger']).get_logger()


class PlatformRegistry:
    """
    Singleton registry for managing MCP servers and clients across the platform.

    This class provides a centralized interface for registering platform tools
    as MCP servers, managing their lifecycle, and providing client access.
    Uses the new simplified architecture with ephemeral connections.
    """

    _instance = None
    _directory = None
    _client = None
    _server_host = None
    _initialized = False

    def __new__(cls):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize new components
            cls._directory = MCPDirectory()
            cls._client = ClientExecutor(cls._directory)
            cls._server_host = ServerHost(cls._directory)
            logger.info("Platform MCP Registry singleton created with new architecture")
        return cls._instance

    @property
    def directory(self) -> MCPDirectory:
        """Get the MCP directory."""
        return self._directory

    @property
    def client(self) -> ClientExecutor:
        """Get the MCP client."""
        return self._client

    @property
    def client_proxy(self) -> ClientExecutor:
        """Compatibility property - returns client."""
        return self._client

    @property
    def server_host(self) -> ServerHost:
        """Get the MCP server host."""
        return self._server_host

    async def register_platform_tool(
        self,
        name: str,
        func: Callable,
        _config: Dict[str, Any],
        description: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None
    ):
        """
        Register and host a platform tool as an internal MCP server.

        This method uses the new MCPServerHost to create a FastMCP server
        that hosts the provided function as a tool.
        """
        try:
            logger.info(f"Registering platform tool: {name}")

            # Extract host and port from config
            host = _config.get("ip", _config.get("host", "localhost"))
            port = _config.get("port", 8000)

            # Use MCPServerHost to create and host the tool
            server = await self._server_host.host_platform_tool(
                name=name,
                func=func,
                port=port,
                host=host,
                description=description,
                auth_config=auth_config
            )

            logger.info(f"Successfully registered and started platform tool: {name}")
            return server

        except Exception as e:
            logger.error(f"Failed to register platform tool '{name}': {e}")
            raise

    async def register_external_server(
        self,
        name: str,
        url: str,
        transport: str = "sse",
        headers: Optional[Dict[str, str]] = None,
        auth_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register an external MCP server in the directory."""
        try:
            logger.info(f"Registering external server: {name} at {url}")

            # Create server configuration
            server_config = ServerConfig(
                name=name,
                accessibility="external",
                hosting="remote",
                transport=transport,
                url=url,
                auth=auth_config,
                description=f"External {transport} server at {url}"
            )

            # Register in directory
            self._directory.register(server_config)

            logger.info(f"Successfully registered external server: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register external server '{name}': {e}")
            return False

    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Start all hosted servers.

        In the new architecture, servers are started when hosted,
        so this is mainly for compatibility.
        """
        hosted_servers = self._server_host.list_hosted_servers()
        results = {}

        for server_info in hosted_servers:
            name = server_info["name"]
            results[name] = server_info["running"]
            if server_info["running"]:
                logger.info(f"Server '{name}' is running")
            else:
                logger.warning(f"Server '{name}' is not running")

        return results

    async def get_tool_client(self, name: str) -> ClientExecutor:
        """
        Get a client for making requests to a server.

        Note: Returns the shared client, not a server-specific client.
        Clients are ephemeral and created per-request in the new architecture.
        """
        if name not in self._directory.list_servers():
            logger.error(f"Server '{name}' not found in directory")
            return None

        return self._client

    async def discover_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all available tools from registered servers."""
        results = {}

        for config in self._directory.list_servers():
            try:
                tools = await self._client.list_tools(config.name)
                results[config.name] = tools
            except Exception as e:
                logger.error(f"Failed to discover tools for '{config.name}': {e}")
                results[config.name] = []

        return results

    async def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Invoke a tool on a registered server using ephemeral connection."""
        return await self._client.invoke_tool(server_name, tool_name, arguments)

    def list_servers(
        self,
        accessibility_filter: Optional[str] = None,
        hosting_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all registered servers with optional filtering."""
        configs = self._directory.list_servers(
            accessibility_filter=accessibility_filter,
            hosting_filter=hosting_filter
        )

        # Convert to dict format for compatibility
        return [
            {
                "name": config.name,
                "accessibility": config.accessibility,
                "hosting": config.hosting,
                "transport": config.transport,
                "url": config.url
            }
            for config in configs
        ]

    async def cleanup(self):
        """Clean up all resources managed by the platform registry."""
        logger.info("Cleaning up platform registry resources")
        await self._server_host.stop_all()
        self._initialized = False

    @classmethod
    async def reset_singleton(cls):
        """Reset the singleton instance. Used for testing."""
        if cls._instance is not None:
            # Clean up existing instance
            if cls._server_host is not None:
                await cls._server_host.stop_all()

            # Reset all class variables
            cls._instance = None
            cls._directory = None
            cls._client = None
            cls._server_host = None
            cls._initialized = False

            logger.info("Platform registry singleton reset")

    def is_initialized(self) -> bool:
        """Check if the platform registry has been initialized."""
        return self._initialized

    def mark_initialized(self):
        """Mark the platform registry as initialized."""
        self._initialized = True
        logger.info("Platform registry marked as initialized")

    # Compatibility properties for old code
    @property
    def registry(self):
        """Compatibility property - returns self as mock registry."""
        class CompatRegistry:
            def __init__(self, platform):
                self.platform = platform
                self.servers = {}  # Empty for compatibility

            async def invoke_tool(self, server_name, tool_name, arguments=None):
                return await self.platform.invoke_tool(server_name, tool_name, arguments)

            def list_servers(self, **kwargs):
                return self.platform.list_servers(**kwargs)

        return CompatRegistry(self)


# Global singleton instance
platform_registry = PlatformRegistry()


def main(local=True):
    """Main function that serves as the entry point for the application."""
    if local:
        return {"status": "Platform MCP Registry is running"}
    return None


if __name__ == "__main__":
    main(True)