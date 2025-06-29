#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Registry

Central registry for managing MCP servers in the platform.
Handles both locally-hosted and remote MCP servers with configurable accessibility.
"""
import asyncio
from typing import Dict, List, Optional, Any, Literal
from pathlib import Path

from src.lib.core.log import Logger
from src.lib.core.config import Config
from src.lib.system_services.mcp_client import MCPClient
from src.lib.system_services.mcp_server import MCPServer

logger = Logger().get_logger()


class ServerEntry:
    """Registry entry for an MCP server."""

    def __init__(
        self,
        name: str,
        accessibility: Literal["internal", "external", "both"],
        hosting: Literal["local", "remote"],
        config: Dict[str, Any]
    ):
        self.name = name
        self.accessibility = accessibility
        self.hosting = hosting
        self.config = config
        self.client: Optional[MCPClient] = None
        self.server: Optional[MCPServer] = None  # Only for local hosting
        self.process = None  # For locally hosted external servers


class MCPRegistry:
    """
    Registry for MCP servers based on two properties:
    - Accessibility: who can access it (internal/external/both)
    - Hosting: where it runs (local/remote)
    """

    def __init__(self, config_file: Optional[str] = None):
        self.servers: Dict[str, ServerEntry] = {}
        self.logger = logger
        self.config = {}
        if config_file:
            self.config = Config(config_file=config_file).get_settings()
            if self.config and self.config.get('mcp_servers'):
                asyncio.run(self.register_servers_from_config())

    async def register_servers_from_config(self):
        """Register all servers defined in the configuration file."""
        servers = self.config.get('mcp_servers', [])
        for server_config in servers:
            try:
                await self.register_server(
                    name=server_config['name'],
                    accessibility=server_config['accessibility'],
                    hosting=server_config['hosting'],
                    config=server_config.get('config', {})
                )
            except KeyError as e:
                self.logger.error(f"Missing key in server config: {e}. Server '{server_config.get('name')}' not registered.")
            except Exception as e:
                self.logger.error(f"Failed to register server '{server_config.get('name')}' from config: {e}")

    async def register_server(
        self,
        name: str,
        accessibility: Literal["internal", "external", "both"],
        hosting: Literal["local", "remote"],
        config: Dict[str, Any]
    ) -> bool:
        """
        Register an MCP server.

        Args:
            name: Unique server identifier
            accessibility: Who can access the server
            hosting: Where the server runs
            config: Server configuration
                For local: command, args, env, transport (optional)
                For remote: url, transport, headers (optional)

        Returns:
            True if registration successful
        """
        try:
            if name in self.servers:
                self.logger.warning(f"Server '{name}' already registered, updating")

            entry = ServerEntry(name, accessibility, hosting, config)
            self.servers[name] = entry

            self.logger.info(f"Registered {hosting} {accessibility} server: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register server '{name}': {e}")
            return False

    async def start_server(self, name: str) -> bool:
        """
        Start a locally-hosted server.

        Args:
            name: Server name

        Returns:
            True if started successfully
        """
        if name not in self.servers:
            self.logger.error(f"Server '{name}' not found")
            return False

        entry = self.servers[name]

        if entry.hosting != "local":
            self.logger.debug(f"Server '{name}' is remote, nothing to start")
            return True

        try:
            # For platform internal servers using our MCPServer wrapper
            if entry.config.get("use_internal_server", False):
                transport = entry.config.get("transport", "stdio")
                entry.server = MCPServer(name, transport)

                # Allow registration of tools before starting
                if "setup_callback" in entry.config:
                    await entry.config["setup_callback"](entry.server)

                await entry.server.start(
                    host=entry.config.get("host", "localhost"),
                    port=entry.config.get("port", 8000)
                )
            else:
                # For external MCP servers, just track that we expect stdio
                self.logger.info(f"Server '{name}' configured for local hosting")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start server '{name}': {e}")
            return False

    async def get_client(self, name: str) -> Optional[MCPClient]:
        """
        Get a client connection to a server.

        Args:
            name: Server name

        Returns:
            Connected MCPClient instance
        """
        if name not in self.servers:
            self.logger.error(f"Server '{name}' not found")
            return None

        entry = self.servers[name]

        # Reuse existing client if available
        if entry.client and entry.client._session:
            return entry.client

        try:
            # Create appropriate client based on hosting
            if entry.hosting == "local":
                # Local servers use stdio
                transport = entry.config.get("transport", "stdio")
                if transport == "stdio":
                    client = MCPClient(
                        name=name,
                        transport="stdio",
                        command=entry.config["command"],
                        args=entry.config.get("args", []),
                        env=entry.config.get("env"),
                        cwd=entry.config.get("cwd")
                    )
                else:
                    # Local HTTP-based server
                    client = MCPClient(
                        name=name,
                        transport=transport,
                        url=f"http://{entry.config.get('host', 'localhost')}:{entry.config.get('port', 8000)}/mcp"
                    )
            else:
                # Remote servers
                client = MCPClient(
                    name=name,
                    transport=entry.config["transport"],
                    url=entry.config["url"],
                    headers=entry.config.get("headers")
                )

            await client.connect()
            entry.client = client
            return client

        except Exception as e:
            self.logger.error(f"Failed to create client for '{name}': {e}")
            return None

    async def discover_tools(
        self,
        accessibility_filter: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover tools from registered servers.

        Args:
            accessibility_filter: Filter by accessibility (internal/external/both)

        Returns:
            Dictionary mapping server names to their tools
        """
        results = {}

        for name, entry in self.servers.items():
            # Apply accessibility filter
            if accessibility_filter:
                if accessibility_filter == "external" and entry.accessibility == "internal":
                    continue
                if accessibility_filter == "internal" and entry.accessibility == "external":
                    continue

            try:
                client = await self.get_client(name)
                if client:
                    tools = await client.list_tools()
                    results[name] = tools
            except Exception as e:
                self.logger.error(f"Failed to discover tools for '{name}': {e}")
                results[name] = []

        return results

    async def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Invoke a tool on a specific server.

        Args:
            server_name: Server containing the tool
            tool_name: Tool to invoke
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        client = await self.get_client(server_name)
        if not client:
            raise ValueError(f"Cannot connect to server '{server_name}'")

        return await client.invoke_tool(tool_name, arguments)

    def list_servers(
        self,
        accessibility_filter: Optional[str] = None,
        hosting_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List registered servers with optional filtering.

        Args:
            accessibility_filter: Filter by accessibility
            hosting_filter: Filter by hosting type

        Returns:
            List of server information
        """
        results = []

        for name, entry in self.servers.items():
            if accessibility_filter and entry.accessibility != accessibility_filter:
                continue
            if hosting_filter and entry.hosting != hosting_filter:
                continue

            results.append({
                "name": name,
                "accessibility": entry.accessibility,
                "hosting": entry.hosting,
                "connected": entry.client is not None
            })

        return results

    async def cleanup(self):
        """Clean up all connections and resources."""
        for entry in self.servers.values():
            if entry.client:
                await entry.client.disconnect()
            if entry.server:
                await entry.server.stop()
