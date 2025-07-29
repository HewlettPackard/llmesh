#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compatibility shim for MCPRegistry.

This module maintains backward compatibility by redirecting to the new
simplified MCP architecture components.
"""

from typing import Dict, List, Optional, Any, Literal
from src.lib.services.mcp.mcp_directory import MCPDirectory, ServerConfig
from src.lib.services.mcp.client_executor import ClientExecutor
from src.lib.services.mcp.server_host import ServerHost
from src.lib.services.core.log import Logger

logger = Logger().get_logger()

class MCPRegistry:
    """
    Compatibility wrapper for MCPRegistry.

    Redirects old registry calls to new simplified architecture.
    """

    def __init__(self, config_file: Optional[str] = None):
        """Initialize with new components."""
        self.directory = MCPDirectory()
        self.client_executor = ClientExecutor(self.directory)
        self.server_host = ServerHost(self.directory)

        if config_file:
            logger.warning("Config file loading not implemented in compatibility shim")

    async def register_server(
        self,
        name: str,
        accessibility: Literal["internal", "external", "both"],
        hosting: Literal["local", "remote"],
        config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register server using new architecture."""
        try:
            # Create ServerConfig
            transport = config.get("transport", "stdio")

            server_config = ServerConfig(
                name=name,
                accessibility=accessibility,
                hosting=hosting,
                transport=transport,
                command=config.get("command"),
                args=config.get("args", []),
                env=config.get("env"),
                url=config.get("url"),
                auth=auth_config,
                description=config.get("description")
            )

            # Register in directory
            self.directory.register(server_config)

            return True

        except Exception as e:
            logger.error(f"Failed to register server '{name}': {e}")
            return False

    async def get_client_executor(self, name: str) -> Optional["ClientExecutor"]:
        """Get client - returns compatibility wrapper."""
        if name not in self.directory:
            logger.error(f"Server '{name}' not found")
            return None

        # Return compatibility wrapper
        return ClientExecutor(self.directory)

    async def discover_tools(
        self,
        accessibility_filter: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Discover tools from registered servers."""
        results = {}

        servers = self.directory.list_servers(accessibility_filter=accessibility_filter)
        for config in servers:
            try:
                tools = await self.client_executor.list_tools(config.name)
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
        """Invoke tool using client executor."""
        return await self.client_executor.invoke_tool(server_name, tool_name, arguments)

    def list_servers(
        self,
        accessibility_filter: Optional[str] = None,
        hosting_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List servers using directory."""
        return self.directory.list_servers(
            accessibility_filter=accessibility_filter,
            hosting_filter=hosting_filter
        )

    async def cleanup(self):
        """Clean up - stop hosted servers."""
        await self.server_host.stop_all()
