#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Directory module for managing Model Context Protocol server configurations.

This module provides a simple directory service for storing and retrieving
MCP server configurations. It maintains a registry of available servers
without managing their lifecycle or connections.

Example:
    Basic usage:

    .. code-block:: python

        from src.lib.services.mcp_directory import MCPDirectory, ServerConfig

        # Create directory
        directory = MCPDirectory()

        # Register a server
        config = ServerConfig(
            name="filesystem",
            accessibility="internal",
            hosting="local",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"]
        )
        directory.register("filesystem", config)

        # Retrieve configuration
        fs_config = directory.get("filesystem")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from src.lib.services.core.log import Logger

logger = Logger().get_logger()


@dataclass
class ServerConfig:
    """
    Configuration for an MCP server.

    This dataclass stores all necessary information to connect to an MCP server,
    including transport-specific parameters and authentication settings.

    Attributes:
        name (str): Unique server identifier.
        accessibility (str): Who can access the server ("internal", "external", "both").
        hosting (str): Where the server runs ("local", "remote").
        transport (str): Connection transport ("stdio", "sse", "streamable").
        command (str, optional): Executable command for stdio transport.
        args (list[str], optional): Command arguments for stdio transport.
        env (dict[str, str], optional): Environment variables for stdio transport.
        url (str, optional): Server URL for HTTP transports.
        auth (dict, optional): Authentication configuration.
        description (str, optional): Human-readable server description.
        capabilities (list[str], optional): List of server capabilities.
    """
    name: str
    accessibility: Literal["internal", "external", "both"]
    hosting: Literal["local", "remote"]
    transport: Literal["stdio", "sse", "streamable"]

    # For stdio transport
    command: Optional[str] = None
    args: Optional[List[str]] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None

    # For HTTP transports (sse, streamable)
    url: Optional[str] = None

    # Authentication configuration
    auth: Optional[Dict[str, Any]] = None

    # Metadata
    description: Optional[str] = None
    capabilities: Optional[List[str]] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate transport-specific requirements
        if self.transport == "stdio":
            if not self.command:
                raise ValueError(f"Server '{self.name}': stdio transport requires 'command'")
        elif self.transport in ["sse", "streamable"]:
            if not self.url:
                raise ValueError(f"Server '{self.name}': {self.transport} transport requires 'url'")

        # Validate hosting/transport combinations
        if self.hosting == "remote" and self.transport == "stdio":
            raise ValueError(f"Server '{self.name}': remote hosting incompatible with stdio transport")


class MCPDirectory:
    """
    Simple directory service for MCP server configurations.

    This class provides a centralized registry for storing and retrieving
    MCP server configurations. It does not manage server lifecycle or
    connections - it's purely a configuration store.

    Attributes:
        servers (dict): Dictionary mapping server names to their configurations.
    """

    def __init__(self):
        """Initialize an empty directory."""
        self.servers: Dict[str, ServerConfig] = {}
        logger.info("MCP Directory initialized")

    def register(self, config: ServerConfig) -> None:
        """
        Register a server configuration in the directory.

        The server will be registered under the name specified in config.name.

        :param config: Server configuration to register.
        :type config: ServerConfig

        Example:
            .. code-block:: python

                config = ServerConfig(
                    name="my_server",
                    accessibility="internal",
                    hosting="local",
                    transport="streamable",
                    url="http://localhost:8000/mcp"
                )
                directory.register(config)
        """
        self.servers[config.name] = config
        logger.info(f"Registered {config.hosting} {config.transport} server: {config.name}")

    def get(self, name: str) -> Optional[ServerConfig]:
        """
        Retrieve a server configuration by name.

        :param name: Server name to look up.
        :type name: str
        :return: Server configuration if found, None otherwise.
        :rtype: ServerConfig or None
        """
        return self.servers.get(name)

    def list_servers(
        self,
        accessibility_filter: Optional[str] = None,
        hosting_filter: Optional[str] = None,
        transport_filter: Optional[str] = None
    ) -> List[ServerConfig]:
        """
        List registered servers with optional filtering.

        :param accessibility_filter: Filter by accessibility ("internal", "external", "both").
        :type accessibility_filter: str, optional
        :param hosting_filter: Filter by hosting ("local", "remote").
        :type hosting_filter: str, optional
        :param transport_filter: Filter by transport ("stdio", "sse", "streamable").
        :type transport_filter: str, optional
        :return: List of server configurations matching filters.
        :rtype: list[ServerConfig]

        Example:
            .. code-block:: python

                # Get all local servers
                local_servers = directory.list_servers(hosting_filter="local")

                # Get all streamable servers
                http_servers = directory.list_servers(transport_filter="streamable")
        """
        results = []

        for config in self.servers.values():
            # Apply filters
            if accessibility_filter and config.accessibility != accessibility_filter:
                continue
            if hosting_filter and config.hosting != hosting_filter:
                continue
            if transport_filter and config.transport != transport_filter:
                continue

            results.append(config)

        return results

    def remove(self, name: str) -> bool:
        """
        Remove a server configuration from the directory.

        :param name: Server name to remove.
        :type name: str
        :return: True if server was removed, False if not found.
        :rtype: bool
        """
        if name in self.servers:
            del self.servers[name]
            logger.info(f"Removed server: {name}")
            return True
        return False

    def clear(self) -> None:
        """Remove all server configurations from the directory."""
        self.servers.clear()
        logger.info("Cleared all servers from directory")

    def __len__(self) -> int:
        """Return the number of registered servers."""
        return len(self.servers)

    def __contains__(self, name: str) -> bool:
        """Check if a server is registered."""
        return name in self.servers

    def __repr__(self) -> str:
        """Return string representation of the directory."""
        return f"MCPDirectory({len(self.servers)} servers)"