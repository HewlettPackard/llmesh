#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Registry

Registry system for managing MCP server configurations and capability discovery.
This module provides centralized management of MCP servers, caching of capabilities,
and integration with the platform's configuration system.

Architecture Integration:
- Integrates with platform's configuration management
- Provides capability discovery and caching
- Manages multiple MCP server configurations
- Supports dynamic server registration and discovery
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field

from src.lib.core.log import Logger
from src.lib.core.config import Config as PlatformConfig
from .client import MCPClient, MCPClientManager

logger = Logger().get_logger()


class MCPRegistry:
    """
    Registry for managing MCP server configurations and capabilities.

    This class provides centralized management of MCP servers, including
    configuration storage, capability discovery, and caching functionality.
    """

    class ServerConfig(BaseModel):
        """
        Configuration for a registered MCP server.
        """
        name: str = Field(
            ...,
            description="Unique name identifier for the server"
        )
        transport: str = Field(
            ...,
            description="Transport type: 'stdio' or 'sse'"
        )
        enabled: bool = Field(
            default=True,
            description="Whether this server is enabled"
        )

        # Transport-specific configurations
        command: Optional[str] = Field(
            default=None,
            description="Command for STDIO transport"
        )
        args: Optional[List[str]] = Field(
            default=None,
            description="Arguments for STDIO transport"
        )
        url: Optional[str] = Field(
            default=None,
            description="URL for SSE transport"
        )

        # Capability caching
        last_discovery: Optional[datetime] = Field(
            default=None,
            description="Timestamp of last capability discovery"
        )
        capabilities: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Cached server capabilities"
        )

        # Metadata
        description: Optional[str] = Field(
            default=None,
            description="Human-readable description of the server"
        )
        tags: Optional[List[str]] = Field(
            default=None,
            description="Tags for categorizing the server"
        )

    class Config(BaseModel):
        """
        Configuration for MCP Registry.
        """
        registry_file: Optional[str] = Field(
            default="mcp_registry.json",
            description="File path for storing registry data"
        )
        cache_ttl: int = Field(
            default=300,
            description="Cache TTL in seconds for capability discovery"
        )
        auto_discovery: bool = Field(
            default=True,
            description="Enable automatic capability discovery"
        )
        discovery_timeout: int = Field(
            default=30,
            description="Timeout for capability discovery in seconds"
        )

    def __init__(self, config: Union[Dict, Config, None] = None):
        """
        Initialize the MCP registry.

        Args:
            config: Registry configuration
        """
        if config is None:
            config = {}

        if isinstance(config, dict):
            self.config = self.Config(**config)
        else:
            self.config = config

        self.logger = logger
        self._servers: Dict[str, self.ServerConfig] = {}
        self._client_managers: Dict[str, MCPClientManager] = {}

        # Load existing registry data
        self._load_registry()

    def register_server(self, server_config: Union[Dict, ServerConfig]) -> bool:
        """
        Register a new MCP server.

        Args:
            server_config: Server configuration

        Returns:
            True if registration successful, False otherwise
        """
        try:
            if isinstance(server_config, dict):
                config = self.ServerConfig(**server_config)
            else:
                config = server_config

            if config.name in self._servers:
                self.logger.warning(f"Server '{config.name}' already registered, updating configuration")

            self._servers[config.name] = config
            self.logger.info(f"Registered MCP server: {config.name}")

            # Save to persistent storage
            self._save_registry()

            # Create client manager if enabled
            if config.enabled:
                self._create_client_manager(config)

            return True

        except Exception as e:
            self.logger.error(f"Failed to register server: {str(e)}")
            return False

    def unregister_server(self, server_name: str) -> bool:
        """
        Unregister an MCP server.

        Args:
            server_name: Name of the server to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if server_name not in self._servers:
                self.logger.warning(f"Server '{server_name}' not found in registry")
                return False

            # Remove client manager
            if server_name in self._client_managers:
                del self._client_managers[server_name]

            # Remove from registry
            del self._servers[server_name]
            self.logger.info(f"Unregistered MCP server: {server_name}")

            # Save to persistent storage
            self._save_registry()
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister server '{server_name}': {str(e)}")
            return False

    def get_server(self, server_name: str) -> Optional[ServerConfig]:
        """
        Get configuration for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Server configuration if found, None otherwise
        """
        return self._servers.get(server_name)

    def list_servers(self, enabled_only: bool = False, tags: Optional[List[str]] = None) -> List[ServerConfig]:
        """
        List registered servers with optional filtering.

        Args:
            enabled_only: Only return enabled servers
            tags: Filter by tags (server must have at least one matching tag)

        Returns:
            List of server configurations
        """
        servers = list(self._servers.values())

        if enabled_only:
            servers = [s for s in servers if s.enabled]

        if tags:
            servers = [s for s in servers if s.tags and any(tag in s.tags for tag in tags)]

        return servers

    async def discover_capabilities(self, server_name: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Discover capabilities for a specific server.

        Args:
            server_name: Name of the server
            force_refresh: Force refresh even if cache is valid

        Returns:
            Server capabilities if successful, None otherwise
        """
        server_config = self._servers.get(server_name)
        if not server_config or not server_config.enabled:
            self.logger.warning(f"Server '{server_name}' not found or disabled")
            return None

        # Check cache validity
        if not force_refresh and self._is_cache_valid(server_config):
            self.logger.debug(f"Using cached capabilities for '{server_name}'")
            return server_config.capabilities

        try:
            self.logger.info(f"Discovering capabilities for server '{server_name}'")

            # Get or create client manager
            client_manager = self._get_client_manager(server_name)
            if not client_manager:
                return None

            # Discover capabilities
            result = await asyncio.wait_for(
                client_manager.get_capabilities(),
                timeout=self.config.discovery_timeout
            )

            if result.status == "success":
                # Update cache
                server_config.capabilities = result.data
                server_config.last_discovery = datetime.now()
                self._save_registry()

                self.logger.info(f"Successfully discovered capabilities for '{server_name}'")
                return result.data
            else:
                self.logger.error(f"Failed to discover capabilities for '{server_name}': {result.error_message}")
                return None

        except asyncio.TimeoutError:
            self.logger.error(f"Capability discovery timed out for '{server_name}'")
            return None
        except Exception as e:
            self.logger.error(f"Error discovering capabilities for '{server_name}': {str(e)}")
            return None

    async def discover_all_capabilities(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Discover capabilities for all enabled servers.

        Args:
            force_refresh: Force refresh even if cache is valid

        Returns:
            Dictionary mapping server names to their capabilities
        """
        enabled_servers = [s for s in self._servers.values() if s.enabled]

        if not enabled_servers:
            self.logger.info("No enabled servers found for capability discovery")
            return {}

        self.logger.info(f"Discovering capabilities for {len(enabled_servers)} servers")

        # Discover capabilities concurrently
        tasks = [
            self.discover_capabilities(server.name, force_refresh)
            for server in enabled_servers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        capabilities = {}
        for server, result in zip(enabled_servers, results):
            if isinstance(result, Exception):
                self.logger.error(f"Exception during discovery for '{server.name}': {str(result)}")
            elif result is not None:
                capabilities[server.name] = result

        self.logger.info(f"Successfully discovered capabilities for {len(capabilities)} servers")
        return capabilities

    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tools across all registered servers.

        Args:
            query: Search query (matches tool name or description)

        Returns:
            List of matching tools with server information
        """
        matching_tools = []
        query_lower = query.lower()

        for server_name, server_config in self._servers.items():
            if not server_config.enabled or not server_config.capabilities:
                continue

            tools = server_config.capabilities.get('tools', [])
            for tool in tools:
                tool_name = tool.get('name', '').lower()
                tool_desc = tool.get('description', '').lower()

                if query_lower in tool_name or query_lower in tool_desc:
                    matching_tools.append({
                        **tool,
                        'server_name': server_name,
                        'server_transport': server_config.transport
                    })

        return matching_tools

    def get_client_manager(self, server_name: str) -> Optional[MCPClientManager]:
        """
        Get client manager for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Client manager if available, None otherwise
        """
        return self._client_managers.get(server_name)

    def _create_client_manager(self, server_config: ServerConfig) -> Optional[MCPClientManager]:
        """Create client manager for server configuration."""
        try:
            client_config = MCPClient.Config(
                name=server_config.name,
                transport=server_config.transport,
                command=server_config.command,
                args=server_config.args,
                url=server_config.url
            )

            manager = MCPClientManager(client_config)
            self._client_managers[server_config.name] = manager
            return manager

        except Exception as e:
            self.logger.error(f"Failed to create client manager for '{server_config.name}': {str(e)}")
            return None

    def _get_client_manager(self, server_name: str) -> Optional[MCPClientManager]:
        """Get or create client manager for server."""
        if server_name in self._client_managers:
            return self._client_managers[server_name]

        server_config = self._servers.get(server_name)
        if server_config and server_config.enabled:
            return self._create_client_manager(server_config)

        return None

    def _is_cache_valid(self, server_config: ServerConfig) -> bool:
        """Check if cached capabilities are still valid."""
        if not server_config.capabilities or not server_config.last_discovery:
            return False

        cache_age = datetime.now() - server_config.last_discovery
        return cache_age < timedelta(seconds=self.config.cache_ttl)

    def _load_registry(self) -> None:
        """Load registry data from persistent storage."""
        try:
            registry_path = Path(self.config.registry_file)
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    data = json.load(f)

                for server_data in data.get('servers', []):
                    # Convert datetime strings back to datetime objects
                    if 'last_discovery' in server_data and server_data['last_discovery']:
                        server_data['last_discovery'] = datetime.fromisoformat(server_data['last_discovery'])

                    server_config = self.ServerConfig(**server_data)
                    self._servers[server_config.name] = server_config

                    # Create client manager if enabled
                    if server_config.enabled:
                        self._create_client_manager(server_config)

                self.logger.info(f"Loaded {len(self._servers)} servers from registry")
        except Exception as e:
            self.logger.warning(f"Failed to load registry: {str(e)}")

    def _save_registry(self) -> None:
        """Save registry data to persistent storage."""
        try:
            registry_path = Path(self.config.registry_file)
            registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            servers_data = []
            for server_config in self._servers.values():
                server_dict = server_config.model_dump()

                # Convert datetime to string
                if server_dict.get('last_discovery'):
                    server_dict['last_discovery'] = server_dict['last_discovery'].isoformat()

                servers_data.append(server_dict)

            data = {
                'servers': servers_data,
                'updated': datetime.now().isoformat()
            }

            with open(registry_path, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.debug(f"Saved registry to {registry_path}")
        except Exception as e:
            self.logger.error(f"Failed to save registry: {str(e)}")

    def __repr__(self) -> str:
        """String representation of the registry."""
        enabled_count = len([s for s in self._servers.values() if s.enabled])
        return f"MCPRegistry(total={len(self._servers)}, enabled={enabled_count})"