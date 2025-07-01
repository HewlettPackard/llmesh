#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test MCP Registry functionality

Tests for the MCPRegistry class that manages MCP servers.
These tests validate the registry functionality including server registration,
client creation, and tool discovery.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.lib.system_services.mcp_registry import MCPRegistry, ServerEntry
from src.lib.system_services.mcp_client import MCPClient
from src.lib.system_services.mcp_server import MCPServer


class TestServerEntry:
    """Test ServerEntry functionality."""

    def test_server_entry_initialization(self):
        """Test ServerEntry initialization."""
        config = {"command": "python", "args": ["server.py"]}
        entry = ServerEntry(
            name="test_server",
            accessibility="internal",
            hosting="local",
            config=config
        )

        assert entry.name == "test_server"
        assert entry.accessibility == "internal"
        assert entry.hosting == "local"
        assert entry.config == config
        assert entry.client is None
        assert entry.server is None
        assert entry.process is None


class TestMCPRegistryInitialization:
    """Test MCP registry initialization."""

    def test_registry_initialization_without_config(self):
        """Test registry initialization without config file."""
        registry = MCPRegistry()

        assert registry.servers == {}
        assert registry.config == {}

    def test_registry_initialization_with_nonexistent_config(self):
        """Test registry initialization with nonexistent config file."""
        registry = MCPRegistry("/nonexistent/config.yaml")

        assert registry.servers == {}

    @patch('src.lib.system_services.mcp_registry.Config')
    def test_registry_initialization_with_config(self, mock_config_class):
        """Test registry initialization with valid config file."""
        mock_config = Mock()
        mock_config.get_settings.return_value = {
            "mcp_servers": [
                {
                    "name": "test_server",
                    "accessibility": "internal",
                    "hosting": "local",
                    "config": {"command": "python"}
                }
            ]
        }
        mock_config_class.return_value = mock_config

        with patch.object(MCPRegistry, 'register_servers_from_config', new_callable=AsyncMock) as mock_register:
            registry = MCPRegistry("config.yaml")

            assert registry.config == mock_config.get_settings.return_value
            mock_config_class.assert_called_once_with(config_file="config.yaml")


class TestMCPRegistryServerManagement:
    """Test MCP registry server management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = MCPRegistry()

    @pytest.mark.asyncio
    async def test_register_server_success(self):
        """Test successful server registration."""
        config = {"command": "python", "args": ["server.py"]}

        result = await self.registry.register_server(
            name="test_server",
            accessibility="internal",
            hosting="local",
            config=config
        )

        assert result is True
        assert "test_server" in self.registry.servers

        entry = self.registry.servers["test_server"]
        assert entry.name == "test_server"
        assert entry.accessibility == "internal"
        assert entry.hosting == "local"
        assert entry.config == config

    @pytest.mark.asyncio
    async def test_register_server_update_existing(self):
        """Test updating an existing server registration."""
        # Register initial server
        await self.registry.register_server(
            name="test_server",
            accessibility="internal",
            hosting="local",
            config={"command": "python"}
        )

        # Update with new config
        new_config = {"command": "node", "args": ["server.js"]}
        result = await self.registry.register_server(
            name="test_server",
            accessibility="external",
            hosting="remote",
            config=new_config
        )

        assert result is True
        entry = self.registry.servers["test_server"]
        assert entry.accessibility == "external"
        assert entry.hosting == "remote"
        assert entry.config == new_config

    @pytest.mark.asyncio
    async def test_start_server_not_found(self):
        """Test starting a server that doesn't exist."""
        result = await self.registry.start_server("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_start_remote_server(self):
        """Test starting a remote server (should be no-op)."""
        await self.registry.register_server(
            name="remote_server",
            accessibility="external",
            hosting="remote",
            config={"url": "http://example.com", "transport": "sse"}
        )

        result = await self.registry.start_server("remote_server")
        assert result is True

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_registry.MCPServer')
    async def test_start_internal_server_success(self, mock_server_class):
        """Test starting an internal server successfully."""
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server

        setup_callback = AsyncMock()

        await self.registry.register_server(
            name="internal_server",
            accessibility="internal",
            hosting="local",
            config={
                "use_internal_server": True,
                "transport": "stdio",
                "host": "localhost",
                "port": 8080,
                "setup_callback": setup_callback
            }
        )

        result = await self.registry.start_server("internal_server")

        assert result is True
        mock_server_class.assert_called_once_with(
            "internal_server",
            "stdio",
            token_verifier=None,
            auth_settings=None
        )
        setup_callback.assert_called_once_with(mock_server)
        mock_server.start.assert_called_once_with(host="localhost", port=8080)

        # Verify server is stored in entry
        entry = self.registry.servers["internal_server"]
        assert entry.server == mock_server

    def test_list_servers_no_filters(self):
        """Test listing all servers without filters."""
        # Setup some servers
        server1 = ServerEntry("server1", "internal", "local", {})
        server2 = ServerEntry("server2", "external", "remote", {})
        server3 = ServerEntry("server3", "both", "local", {})

        self.registry.servers = {
            "server1": server1,
            "server2": server2,
            "server3": server3
        }

        servers = self.registry.list_servers()

        assert len(servers) == 3
        server_names = [s["name"] for s in servers]
        assert "server1" in server_names
        assert "server2" in server_names
        assert "server3" in server_names

    def test_list_servers_with_accessibility_filter(self):
        """Test listing servers with accessibility filter."""
        # Setup servers
        server1 = ServerEntry("server1", "internal", "local", {})
        server2 = ServerEntry("server2", "external", "remote", {})
        server3 = ServerEntry("server3", "both", "local", {})

        self.registry.servers = {
            "server1": server1,
            "server2": server2,
            "server3": server3
        }

        # Test internal filter
        internal_servers = self.registry.list_servers(accessibility_filter="internal")
        assert len(internal_servers) == 1
        assert internal_servers[0]["name"] == "server1"

        # Test external filter
        external_servers = self.registry.list_servers(accessibility_filter="external")
        assert len(external_servers) == 1
        assert external_servers[0]["name"] == "server2"

    def test_list_servers_with_hosting_filter(self):
        """Test listing servers with hosting filter."""
        # Setup servers
        server1 = ServerEntry("server1", "internal", "local", {})
        server2 = ServerEntry("server2", "external", "remote", {})
        server3 = ServerEntry("server3", "both", "local", {})

        self.registry.servers = {
            "server1": server1,
            "server2": server2,
            "server3": server3
        }

        # Test local filter
        local_servers = self.registry.list_servers(hosting_filter="local")
        assert len(local_servers) == 2
        local_names = [s["name"] for s in local_servers]
        assert "server1" in local_names
        assert "server3" in local_names

        # Test remote filter
        remote_servers = self.registry.list_servers(hosting_filter="remote")
        assert len(remote_servers) == 1
        assert remote_servers[0]["name"] == "server2"


class TestMCPRegistryClientManagement:
    """Test MCP registry client management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = MCPRegistry()

    @pytest.mark.asyncio
    async def test_get_client_server_not_found(self):
        """Test getting client for nonexistent server."""
        client = await self.registry.get_client("nonexistent")
        assert client is None

    @pytest.mark.asyncio
    async def test_get_client_reuse_existing(self):
        """Test reusing existing client connection."""
        # Setup server entry with existing client
        entry = ServerEntry("test_server", "internal", "local", {})
        mock_client = Mock()
        mock_client._session = Mock()  # Simulate connected client
        entry.client = mock_client

        self.registry.servers["test_server"] = entry

        client = await self.registry.get_client("test_server")
        assert client == mock_client

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_registry.MCPClient')
    async def test_get_client_local_stdio_server(self, mock_client_class):
        """Test getting client for local STDIO server."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        await self.registry.register_server(
            name="local_server",
            accessibility="internal",
            hosting="local",
            config={
                "command": "python",
                "args": ["server.py"],
                "env": {"TEST": "value"},
                "cwd": "/test"
            }
        )

        client = await self.registry.get_client("local_server")

        assert client == mock_client
        mock_client_class.assert_called_once_with(
            name="local_server",
            transport="stdio",
            command="python",
            args=["server.py"],
            env={"TEST": "value"},
            cwd="/test",
            auth_config=None
        )
        mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_registry.MCPClient')
    async def test_get_client_local_http_server(self, mock_client_class):
        """Test getting client for local HTTP server."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        await self.registry.register_server(
            name="http_server",
            accessibility="external",
            hosting="local",
            config={
                "transport": "sse",
                "host": "localhost",
                "port": 8080
            }
        )

        client = await self.registry.get_client("http_server")

        assert client == mock_client
        mock_client_class.assert_called_once_with(
            name="http_server",
            transport="sse",
            url="http://localhost:8080/mcp",
            auth_config=None
        )
        mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_registry.MCPClient')
    async def test_get_client_remote_server(self, mock_client_class):
        """Test getting client for remote server."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        await self.registry.register_server(
            name="remote_server",
            accessibility="external",
            hosting="remote",
            config={
                "transport": "streamable",
                "url": "https://api.example.com/mcp",
                "headers": {"Authorization": "Bearer token"}
            }
        )

        client = await self.registry.get_client("remote_server")

        assert client == mock_client
        mock_client_class.assert_called_once_with(
            name="remote_server",
            transport="streamable",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"},
            auth_config=None
        )
        mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_registry.MCPClient')
    async def test_get_client_connection_failure(self, mock_client_class):
        """Test handling client connection failure."""
        mock_client = AsyncMock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        await self.registry.register_server(
            name="failing_server",
            accessibility="internal",
            hosting="local",
            config={"command": "python"}
        )

        client = await self.registry.get_client("failing_server")
        assert client is None


class TestMCPRegistryToolOperations:
    """Test MCP registry tool discovery and invocation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = MCPRegistry()

    @pytest.mark.asyncio
    async def test_discover_tools_no_servers(self):
        """Test tool discovery with no registered servers."""
        tools = await self.registry.discover_tools()
        assert tools == {}

    @pytest.mark.asyncio
    async def test_discover_tools_with_accessibility_filter(self):
        """Test tool discovery with accessibility filter."""
        # Setup servers
        await self.registry.register_server(
            name="internal_server",
            accessibility="internal",
            hosting="local",
            config={"command": "python"}
        )
        await self.registry.register_server(
            name="external_server",
            accessibility="external",
            hosting="remote",
            config={"url": "http://example.com", "transport": "sse"}
        )
        await self.registry.register_server(
            name="both_server",
            accessibility="both",
            hosting="local",
            config={"command": "node"}
        )

        # Mock get_client to return mock clients with tools
        mock_client1 = AsyncMock()
        mock_client1.list_tools.return_value = [{"name": "internal_tool"}]

        mock_client2 = AsyncMock()
        mock_client2.list_tools.return_value = [{"name": "external_tool"}]

        mock_client3 = AsyncMock()
        mock_client3.list_tools.return_value = [{"name": "both_tool"}]

        with patch.object(self.registry, 'get_client') as mock_get_client:
            async def get_client_side_effect(name):
                if name == "internal_server":
                    return mock_client1
                elif name == "external_server":
                    return mock_client2
                elif name == "both_server":
                    return mock_client3
                else:
                    return None

            mock_get_client.side_effect = get_client_side_effect

            # Test internal filter
            tools = await self.registry.discover_tools(accessibility_filter="internal")

            # Should include internal and both servers, but not external
            assert "internal_server" in tools
            assert "both_server" in tools
            assert "external_server" not in tools

            # Test external filter
            tools = await self.registry.discover_tools(accessibility_filter="external")

            # Should include external and both servers, but not internal
            assert "internal_server" not in tools
            assert "both_server" in tools
            assert "external_server" in tools

    @pytest.mark.asyncio
    async def test_invoke_tool_success(self):
        """Test successful tool invocation."""
        await self.registry.register_server(
            name="test_server",
            accessibility="internal",
            hosting="local",
            config={"command": "python"}
        )

        mock_client = AsyncMock()
        mock_client.invoke_tool.return_value = "tool result"

        with patch.object(self.registry, 'get_client', return_value=mock_client):
            result = await self.registry.invoke_tool(
                "test_server",
                "test_tool",
                {"arg": "value"}
            )

            assert result == "tool result"
            mock_client.invoke_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_invoke_tool_client_not_found(self):
        """Test tool invocation when client cannot be created."""
        await self.registry.register_server(
            name="test_server",
            accessibility="internal",
            hosting="local",
            config={"command": "python"}
        )

        with patch.object(self.registry, 'get_client', return_value=None):
            with pytest.raises(ValueError, match="Cannot connect to server 'test_server'"):
                await self.registry.invoke_tool("test_server", "test_tool", {})


class TestMCPRegistryCleanup:
    """Test MCP registry cleanup functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = MCPRegistry()

    @pytest.mark.asyncio
    async def test_cleanup_no_connections(self):
        """Test cleanup with no active connections."""
        await self.registry.cleanup()
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_cleanup_with_clients_and_servers(self):
        """Test cleanup with active clients and servers."""
        # Create mock entries with clients and servers
        entry1 = ServerEntry("server1", "internal", "local", {})
        entry1.client = AsyncMock()
        entry1.server = AsyncMock()

        entry2 = ServerEntry("server2", "external", "remote", {})
        entry2.client = AsyncMock()
        # No server for remote entry

        entry3 = ServerEntry("server3", "internal", "local", {})
        # No client or server

        self.registry.servers = {
            "server1": entry1,
            "server2": entry2,
            "server3": entry3
        }

        await self.registry.cleanup()

        # Verify cleanup was called on existing clients and servers
        entry1.client.disconnect.assert_called_once()
        entry1.server.stop.assert_called_once()
        entry2.client.disconnect.assert_called_once()
        # entry2.server should not exist, so no stop call
        # entry3 has no client or server, so no calls


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])