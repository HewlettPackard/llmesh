#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test MCP Client functionality

Tests for MCP client factory, configuration, and manager functionality.
These tests validate the MCP client implementation against the official SDK.
"""

import pytest
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.lib.services.mcp.client import MCPClient, MCPClientManager


class TestMCPClientFactory:
    """Test MCP client factory functionality."""

    def test_create_from_dict_config(self):
        """Test creating client manager from dictionary configuration."""
        config = {
            "name": "test_client",
            "transport": "stdio",
            "command": "python",
            "args": ["test_server.py"]
        }

        manager = MCPClient.create(config)

        assert isinstance(manager, MCPClientManager)
        assert manager.name == "test_client"
        assert manager.transport == "stdio"
        assert manager.config.command == "python"
        assert manager.config.args == ["test_server.py"]

    def test_create_from_config_object(self):
        """Test creating client manager from Config object."""
        config = MCPClient.Config(
            name="test_client",
            transport="sse",
            url="http://localhost:8000/mcp/sse"
        )

        manager = MCPClient.create(config)

        assert isinstance(manager, MCPClientManager)
        assert manager.name == "test_client"
        assert manager.transport == "sse"
        assert manager.config.url == "http://localhost:8000/mcp/sse"

    def test_create_from_file_config(self):
        """Test creating client manager from YAML configuration file."""
        config_content = """
        mcp:
          name: file_test_client
          transport: stdio
          command: python
          args: ["server.py"]
          debug: true
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()

            try:
                manager = MCPClient.create(f.name)

                assert isinstance(manager, MCPClientManager)
                assert manager.name == "file_test_client"
                assert manager.transport == "stdio"
                assert manager.config.debug is True
            finally:
                Path(f.name).unlink()

    def test_get_available_transports(self):
        """Test getting available transport types."""
        transports = MCPClient.get_available_transports()

        assert isinstance(transports, dict)
        assert "stdio" in transports
        assert "sse" in transports
        assert "streamable" in transports
        assert len(transports) >= 3

    def test_create_streamable_client_config(self):
        """Test creating streamable HTTP client configuration."""
        config = {
            "name": "streamable_client",
            "transport": "streamable",
            "url": "http://localhost:8000/mcp",
            "headers": {"Authorization": "Bearer test-token"},
            "timeout": 60
        }

        manager = MCPClient.create(config)

        assert isinstance(manager, MCPClientManager)
        assert manager.name == "streamable_client"
        assert manager.transport == "streamable"
        assert manager.config.url == "http://localhost:8000/mcp"
        assert manager.config.headers == {"Authorization": "Bearer test-token"}
        assert manager.config.timeout == 60

    def test_invalid_config_raises_error(self):
        """Test that invalid configuration raises appropriate errors."""
        with pytest.raises(ValueError):
            MCPClient.create({})  # Missing required fields

        with pytest.raises(ValueError):
            MCPClient.create({"name": "test"})  # Missing transport


class TestMCPClientManager:
    """Test MCP client manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stdio_config = MCPClient.Config(
            name="test_stdio",
            transport="stdio",
            command="python",
            args=["test_server.py"],
            debug=True
        )

        self.sse_config = MCPClient.Config(
            name="test_sse",
            transport="sse",
            url="http://localhost:8000/mcp/sse",
            debug=True
        )

        self.streamable_config = MCPClient.Config(
            name="test_streamable",
            transport="streamable",
            url="http://localhost:8000/mcp",
            headers={"User-Agent": "test-client"},
            timeout=45,
            debug=True
        )

    def test_stdio_manager_initialization(self):
        """Test STDIO client manager initialization."""
        manager = MCPClientManager(self.stdio_config)

        assert manager.name == "test_stdio"
        assert manager.transport == "stdio"
        assert manager.config.command == "python"
        assert manager.config.args == ["test_server.py"]
        assert manager._session is None

    def test_sse_manager_initialization(self):
        """Test SSE client manager initialization."""
        manager = MCPClientManager(self.sse_config)

        assert manager.name == "test_sse"
        assert manager.transport == "sse"
        assert manager.config.url == "http://localhost:8000/mcp/sse"
        assert manager._session is None

    def test_streamable_manager_initialization(self):
        """Test Streamable HTTP client manager initialization."""
        manager = MCPClientManager(self.streamable_config)

        assert manager.name == "test_streamable"
        assert manager.transport == "streamable"
        assert manager.config.url == "http://localhost:8000/mcp"
        assert manager.config.headers == {"User-Agent": "test-client"}
        assert manager.config.timeout == 45
        assert manager._session is None

    @pytest.mark.asyncio
    async def test_stdio_connection_validation(self):
        """Test STDIO connection parameter validation."""
        invalid_config = MCPClient.Config(
            name="invalid_stdio",
            transport="stdio"
            # Missing command
        )

        manager = MCPClientManager(invalid_config)

        with pytest.raises(ValueError, match="STDIO transport requires 'command'"):
            async with manager.connect():
                pass

    @pytest.mark.asyncio
    async def test_sse_connection_validation(self):
        """Test SSE connection parameter validation."""
        invalid_config = MCPClient.Config(
            name="invalid_sse",
            transport="sse"
            # Missing url
        )

        manager = MCPClientManager(invalid_config)

        with pytest.raises(ValueError, match="SSE transport requires 'url'"):
            async with manager.connect():
                pass

    @pytest.mark.asyncio
    async def test_streamable_connection_validation(self):
        """Test Streamable HTTP connection parameter validation."""
        invalid_config = MCPClient.Config(
            name="invalid_streamable",
            transport="streamable"
            # Missing url
        )

        manager = MCPClientManager(invalid_config)

        with pytest.raises(ValueError, match="Streamable transport requires 'url'"):
            async with manager.connect():
                pass

    @pytest.mark.asyncio
    async def test_unsupported_transport_raises_error(self):
        """Test that unsupported transport raises appropriate error."""
        invalid_config = MCPClient.Config(
            name="invalid_transport",
            transport="websocket"  # Not yet implemented
        )

        manager = MCPClientManager(invalid_config)

        with pytest.raises(ValueError, match="Unsupported transport type"):
            async with manager.connect():
                pass

    @pytest.mark.asyncio
    @patch('src.lib.services.mcp.client.stdio_client')
    @patch('src.lib.services.mcp.client.ClientSession')
    async def test_stdio_connection_success(self, mock_session_class, mock_stdio_client):
        """Test successful STDIO connection."""
        # Mock the connection context managers
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = Mock()
        mock_session_context.__aenter__.return_value = mock_session

        manager = MCPClientManager(self.stdio_config)

        async with manager.connect() as session:
            assert session == mock_session
            mock_stdio_client.assert_called_once()
            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.services.mcp.client.sse_client')
    @patch('src.lib.services.mcp.client.ClientSession')
    async def test_sse_connection_success(self, mock_session_class, mock_sse_client):
        """Test successful SSE connection."""
        # Mock the connection context managers
        mock_sse_context = AsyncMock()
        mock_sse_client.return_value = mock_sse_context
        mock_sse_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = Mock()
        mock_session_context.__aenter__.return_value = mock_session

        manager = MCPClientManager(self.sse_config)

        async with manager.connect() as session:
            assert session == mock_session
            mock_sse_client.assert_called_once_with(url=self.sse_config.url)
            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.services.mcp.client.stdio_client')
    @patch('src.lib.services.mcp.client.ClientSession')
    async def test_connection_cleanup(self, mock_session_class, mock_stdio_client):
        """Test that connections are properly cleaned up."""
        # Mock the connection context managers
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = Mock()
        mock_session_context.__aenter__.return_value = mock_session

        manager = MCPClientManager(self.stdio_config)

        async with manager.connect() as session:
            assert session == mock_session

        # Verify cleanup was called
        mock_session_context.__aexit__.assert_called_once()
        mock_stdio_context.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.services.mcp.client.stdio_client')
    @patch('src.lib.services.mcp.client.ClientSession')
    async def test_test_connection_success(self, mock_session_class, mock_stdio_client):
        """Test successful connection test."""
        # Mock successful connection and tool listing
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session

        # Mock successful tool listing
        mock_tools_result = Mock()
        mock_tools_result.tools = [Mock(name="test_tool")]
        mock_session.list_tools.return_value = mock_tools_result

        manager = MCPClientManager(self.stdio_config)
        result = await manager.test_connection()

        assert result.status == "success"
        assert result.data["connected"] is True
        assert result.data["tool_count"] == 1
        assert result.data["transport"] == "stdio"
        assert result.client_name == "test_stdio"

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection test failure handling."""
        invalid_config = MCPClient.Config(
            name="fail_test",
            transport="stdio"
            # Missing required command
        )

        manager = MCPClientManager(invalid_config)
        result = await manager.test_connection()

        assert result.status == "error"
        assert "Connection test failed" in result.error_message
        assert result.error_code == "CONNECTION_TEST_FAILED"
        assert result.client_name == "fail_test"

    @pytest.mark.asyncio
    @patch('src.lib.services.mcp.client.stdio_client')
    @patch('src.lib.services.mcp.client.ClientSession')
    async def test_get_capabilities_success(self, mock_session_class, mock_stdio_client):
        """Test successful capability discovery."""
        # Mock successful connection
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session

        # Mock capability discovery
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object", "properties": {}}

        mock_resource = Mock()
        mock_resource.uri = "test://resource"
        mock_resource.name = "Test Resource"
        mock_resource.description = "A test resource"
        mock_resource.mimeType = "text/plain"

        mock_prompt = Mock()
        mock_prompt.name = "test_prompt"
        mock_prompt.description = "A test prompt"
        mock_prompt.arguments = []

        mock_session.list_tools.return_value = Mock(tools=[mock_tool])
        mock_session.list_resources.return_value = Mock(resources=[mock_resource])
        mock_session.list_prompts.return_value = Mock(prompts=[mock_prompt])

        manager = MCPClientManager(self.stdio_config)
        result = await manager.get_capabilities()

        assert result.status == "success"
        assert len(result.data["tools"]) == 1
        assert len(result.data["resources"]) == 1
        assert len(result.data["prompts"]) == 1

        assert result.data["tools"][0]["name"] == "test_tool"
        assert result.data["resources"][0]["uri"] == "test://resource"
        assert result.data["prompts"][0]["name"] == "test_prompt"

    def test_manager_repr(self):
        """Test string representation of client manager."""
        manager = MCPClientManager(self.stdio_config)
        repr_str = repr(manager)

        assert "MCPClientManager" in repr_str
        assert "test_stdio" in repr_str
        assert "stdio" in repr_str