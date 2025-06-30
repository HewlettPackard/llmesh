#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test MCP Client functionality

Tests for the simplified MCP client implementation.
These tests validate the MCPClient wrapper around the MCP SDK.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.lib.system_services.mcp_client import MCPClient


class TestMCPClientInitialization:
    """Test MCP client initialization and configuration."""

    def test_stdio_client_initialization(self):
        """Test STDIO client initialization."""
        client = MCPClient(
            name="test_stdio",
            transport="stdio",
            command="python",
            args=["test_server.py"]
        )

        assert client.name == "test_stdio"
        assert client.transport == "stdio"
        assert client.connection_params["command"] == "python"
        assert client.connection_params["args"] == ["test_server.py"]
        assert client._session is None

    def test_sse_client_initialization(self):
        """Test SSE client initialization."""
        client = MCPClient(
            name="test_sse",
            transport="sse",
            url="http://localhost:8000/mcp/sse"
        )

        assert client.name == "test_sse"
        assert client.transport == "sse"
        assert client.connection_params["url"] == "http://localhost:8000/mcp/sse"
        assert client._session is None

    def test_streamable_client_initialization(self):
        """Test streamable HTTP client initialization."""
        client = MCPClient(
            name="test_streamable",
            transport="streamable",
            url="http://localhost:8000/mcp",
            headers={"Authorization": "Bearer token"},
            timeout=60
        )

        assert client.name == "test_streamable"
        assert client.transport == "streamable"
        assert client.connection_params["url"] == "http://localhost:8000/mcp"
        assert client.connection_params["headers"] == {"Authorization": "Bearer token"}
        assert client.connection_params["timeout"] == 60
        assert client._session is None

    def test_invalid_transport_raises_error(self):
        """Test that invalid transport raises appropriate error."""
        client = MCPClient(
            name="invalid_transport",
            transport="websocket"  # Not supported
        )

        # Error should occur on connect, not initialization
        assert client.transport == "websocket"


class TestMCPClientConnection:
    """Test MCP client connection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stdio_client = MCPClient(
            name="test_stdio",
            transport="stdio",
            command="python",
            args=["test_server.py"]
        )

        self.sse_client = MCPClient(
            name="test_sse",
            transport="sse",
            url="http://localhost:8000/mcp/sse"
        )

        self.streamable_client = MCPClient(
            name="test_streamable",
            transport="streamable",
            url="http://localhost:8000/mcp",
            headers={"User-Agent": "test-client"},
            timeout=45
        )

    @pytest.mark.asyncio
    async def test_unsupported_transport_raises_error(self):
        """Test that unsupported transport raises appropriate error."""
        client = MCPClient(
            name="invalid_transport",
            transport="websocket"  # Not supported
        )

        with pytest.raises(ValueError, match="Unknown transport"):
            await client.connect()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.stdio_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_stdio_connection_success(self, mock_session_class, mock_stdio_client):
        """Test successful STDIO connection."""
        # Mock the connection context managers
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        await self.stdio_client.connect()

        assert self.stdio_client._session == mock_session
        mock_stdio_client.assert_called_once()
        mock_session_class.assert_called_once()
        mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.sse_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_sse_connection_success(self, mock_session_class, mock_sse_client):
        """Test successful SSE connection."""
        # Mock the connection context managers
        mock_sse_context = AsyncMock()
        mock_sse_client.return_value = mock_sse_context
        mock_sse_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        await self.sse_client.connect()

        assert self.sse_client._session == mock_session
        mock_sse_client.assert_called_once_with(url="http://localhost:8000/mcp/sse", headers={})
        mock_session_class.assert_called_once()
        mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.stdio_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_connection_cleanup(self, mock_session_class, mock_stdio_client):
        """Test that connections are properly cleaned up."""
        # Mock the connection context managers
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        async with self.stdio_client:
            assert self.stdio_client._session == mock_session

        # Verify cleanup was called
        mock_session_context.__aexit__.assert_called_once()
        mock_stdio_context.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.stdio_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_list_tools_success(self, mock_session_class, mock_stdio_client):
        """Test successful tool listing."""
        # Mock successful connection and tool listing
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        # Mock successful tool listing
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object"}

        mock_tools_result = Mock()
        mock_tools_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_tools_result

        tools = await self.stdio_client.list_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["description"] == "A test tool"
        assert tools[0]["inputSchema"] == {"type": "object"}

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.stdio_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_invoke_tool_success(self, mock_session_class, mock_stdio_client):
        """Test successful tool invocation."""
        # Mock successful connection
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        # Mock tool invocation
        mock_result = Mock()
        mock_result.content = ["Tool result"]
        mock_session.call_tool.return_value = mock_result

        result = await self.stdio_client.invoke_tool("test_tool", {"arg": "value"})

        assert result == ["Tool result"]
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.stdio_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_list_resources_success(self, mock_session_class, mock_stdio_client):
        """Test successful resource listing."""
        # Mock successful connection
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        # Mock resource listing
        mock_resource = Mock()
        mock_resource.uri = "test://resource"
        mock_resource.name = "Test Resource"
        mock_resource.description = "A test resource"
        mock_resource.mimeType = "text/plain"

        mock_resources_result = Mock()
        mock_resources_result.resources = [mock_resource]
        mock_session.list_resources.return_value = mock_resources_result

        resources = await self.stdio_client.list_resources()

        assert len(resources) == 1
        assert resources[0]["uri"] == "test://resource"
        assert resources[0]["name"] == "Test Resource"
        assert resources[0]["description"] == "A test resource"
        assert resources[0]["mimeType"] == "text/plain"

    @pytest.mark.asyncio
    @patch('src.lib.system_services.mcp_client.stdio_client')
    @patch('src.lib.system_services.mcp_client.ClientSession')
    async def test_list_prompts_success(self, mock_session_class, mock_stdio_client):
        """Test successful prompt listing."""
        # Mock successful connection
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (Mock(), Mock())

        mock_session_context = AsyncMock()
        mock_session_class.return_value = mock_session_context
        mock_session = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.initialize = AsyncMock()

        # Mock prompt listing
        mock_prompt = Mock()
        mock_prompt.name = "test_prompt"
        mock_prompt.description = "A test prompt"
        mock_prompt.arguments = []

        mock_prompts_result = Mock()
        mock_prompts_result.prompts = [mock_prompt]
        mock_session.list_prompts.return_value = mock_prompts_result

        prompts = await self.stdio_client.list_prompts()

        assert len(prompts) == 1
        assert prompts[0]["name"] == "test_prompt"
        assert prompts[0]["description"] == "A test prompt"
        assert prompts[0]["arguments"] == []

    def test_client_repr(self):
        """Test string representation of client."""
        repr_str = repr(self.stdio_client)

        assert "MCPClient" in repr_str
        assert "test_stdio" in repr_str
        assert "stdio" in repr_str
        assert "connected=False" in repr_str
