#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Platform MCP Registry Singleton

This module provides a singleton registry for managing all MCP servers and clients
across the LLMesh platform. It centralizes the registration, discovery, and
management of platform tools using the Model Context Protocol.
"""

from typing import Dict, Any, Callable, Optional, List

from src.lib.system_services.mcp_registry import MCPRegistry
from src.lib.system_services.mcp_server import MCPServer
from src.lib.system_services.mcp_client import MCPClient
from src.lib.core.log import Logger
from src.lib.core.config import Config


# Load configuration
config = Config('src/platform/mcp/config.yaml').get_settings()
logger = Logger().configure(config['logger']).get_logger()


class PlatformRegistry:
    """
    Singleton registry for managing MCP servers and clients across the platform.

    This class provides a centralized interface for registering platform tools
    as MCP servers, managing their lifecycle, and providing client access.
    """

    _instance = None
    _registry = None
    _initialized = False

    def __new__(cls):
        """
        Create or return the singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._registry = MCPRegistry()
            logger.info("Platform MCP Registry singleton created")
        return cls._instance

    @property
    def registry(self) -> MCPRegistry:
        """
        Get the underlying MCP registry.
        """
        return self._registry

    async def register_platform_tool(
        self,
        name: str,
        func: Callable,
        config: Dict[str, Any],
        description: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None
    ) -> MCPServer:
        """
        Register a platform tool as an internal MCP server.
        """
        try:
            logger.info(f"Registering platform tool: {name}")

            # Create MCP server wrapper
            server = MCPServer(name, "streamable")

            # Register the tool function
            server.register_tool(name, func, description)

            # Create setup callback that preserves the server instance
            async def setup_callback(srv):
                # Server is already configured with the tool
                return srv

            # Register in registry with internal server configuration
            server_config = {
                "use_internal_server": True,
                "transport": "streamable",
                "setup_callback": setup_callback,
                **config  # Include all config parameters (host, port, ssh_cert, etc.)
            }

            await self.registry.register_server(
                name=name,
                accessibility="internal",
                hosting="local",
                config=server_config,
                auth_config=auth_config
            )

            # Store server reference in the registry entry
            entry = self.registry.servers[name]
            entry.server = server

            logger.info(f"Successfully registered platform tool: {name}")
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
        """
        Register an external MCP server.
        """
        try:
            logger.info(f"Registering external server: {name} at {url}")

            config = {
                "url": url,
                "transport": transport
            }
            if headers:
                config["headers"] = headers

            return await self.registry.register_server(
                name=name,
                accessibility="external",
                hosting="remote",
                config=config,
                auth_config=auth_config
            )

        except Exception as e:
            logger.error(f"Failed to register external server '{name}': {e}")
            return False

    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Start all registered local servers.
        """
        results = {}
        local_servers = self.registry.list_servers(hosting_filter="local")

        for server_info in local_servers:
            name = server_info["name"]
            try:
                success = await self.registry.start_server(name)
                results[name] = success
                if success:
                    logger.info(f"Started server: {name}")
                else:
                    logger.warning(f"Failed to start server: {name}")
            except Exception as e:
                logger.error(f"Error starting server '{name}': {e}")
                results[name] = False

        return results

    async def get_tool_client(self, name: str) -> Optional[MCPClient]:
        """
        Get a client for a registered tool.
        """
        try:
            return await self.registry.get_client(name)
        except Exception as e:
            logger.error(f"Failed to get client for tool '{name}': {e}")
            return None

    async def discover_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all available tools from registered servers.
        """
        return await self.registry.discover_tools()

    async def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Invoke a tool on a registered server.
        """
        return await self.registry.invoke_tool(server_name, tool_name, arguments)

    def list_servers(
        self,
        accessibility_filter: Optional[str] = None,
        hosting_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all registered servers with optional filtering.
        """
        return self.registry.list_servers(accessibility_filter, hosting_filter)

    async def cleanup(self):
        """
        Clean up all resources managed by the platform registry.
        """
        logger.info("Cleaning up platform registry resources")
        await self.registry.cleanup()
        self._initialized = False

    def is_initialized(self) -> bool:
        """
        Check if the platform registry has been initialized.
        """
        return self._initialized

    def mark_initialized(self):
        """
        Mark the platform registry as initialized.
        """
        self._initialized = True
        logger.info("Platform registry marked as initialized")


# Global singleton instance
platform_registry = PlatformRegistry()


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    """
    if local:
        return {"status": "Platform MCP Registry is running"}
    return None


if __name__ == "__main__":
    main(True)