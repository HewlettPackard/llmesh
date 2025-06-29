#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test MCP Server functionality

Tests for MCP server wrapper functionality.
These tests validate the MCP server implementation using the FastMCP SDK.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.lib.system_services.mcp_server import MCPServer


class TestMCPServer:
    """Test MCP server functionality."""

    def test_server_initialization(self):
        """Test basic server initialization."""
        server = MCPServer("test_server", "stdio")

        assert server.name == "test_server"
        assert server.transport == "stdio"
        assert server.mcp is not None
        assert server._running is False
        assert server._app is None
        assert server._server_task is None

    def test_server_initialization_different_transports(self):
        """Test server initialization with different transports."""
        # Test stdio
        stdio_server = MCPServer("stdio_server", "stdio")
        assert stdio_server.transport == "stdio"

        # Test sse
        sse_server = MCPServer("sse_server", "sse")
        assert sse_server.transport == "sse"

        # Test streamable
        streamable_server = MCPServer("streamable_server", "streamable")
        assert streamable_server.transport == "streamable"


class TestMCPServerDecorators:
    """Test MCP server decorator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer("test_server", "stdio")

    def test_tool_decorator(self):
        """Test tool registration decorator."""
        @self.server.tool(description="Test tool for addition")
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Verify the tool was registered
        assert callable(add_numbers)
        assert add_numbers(2, 3) == 5

    def test_resource_decorator(self):
        """Test resource registration decorator."""
        @self.server.resource("test://config/{key}")
        def get_config(key: str) -> dict:
            """Get configuration value."""
            return {"key": key, "value": "test_value"}

        # Verify the resource was registered
        assert callable(get_config)
        result = get_config("test_key")
        assert result["key"] == "test_key"

    def test_prompt_decorator(self):
        """Test prompt registration decorator."""
        @self.server.prompt("test_prompt")
        def test_prompt_template(context: str = "default") -> list:
            """Test prompt template."""
            return [f"System: Test prompt with context: {context}"]

        # Verify the prompt was registered
        assert callable(test_prompt_template)
        result = test_prompt_template("custom")
        assert "custom" in result[0]

    def test_register_tool_programmatically(self):
        """Test programmatic tool registration."""
        def multiply_numbers(x: int, y: int) -> int:
            """Multiply two numbers."""
            return x * y

        wrapper = self.server.register_tool(
            "multiply",
            multiply_numbers,
            "Multiply two numbers"
        )

        # Verify the tool was wrapped and works
        assert callable(wrapper)
        assert wrapper.__name__ == "multiply"
        assert wrapper(x=3, y=4) == 12

    @pytest.mark.asyncio
    async def test_register_async_tool_programmatically(self):
        """Test programmatic async tool registration."""
        async def async_add(a: int, b: int) -> int:
            """Add two numbers asynchronously."""
            await asyncio.sleep(0.01)  # Simulate async work
            return a + b

        wrapper = self.server.register_tool(
            "async_add",
            async_add,
            "Add two numbers asynchronously"
        )

        # Verify the async tool was wrapped and works
        assert callable(wrapper)
        assert wrapper.__name__ == "async_add"
        result = await wrapper(a=5, b=7)
        assert result == 12

class TestMCPServerLifecycle:
    """Test MCP server lifecycle functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stdio_server = MCPServer("test_stdio_server", "stdio")
        self.sse_server = MCPServer("test_sse_server", "sse")
        self.streamable_server = MCPServer("test_streamable_server", "streamable")

    def test_server_not_running_initially(self):
        """Test that servers are not running initially."""
        assert not self.stdio_server._running
        assert not self.sse_server._running
        assert not self.streamable_server._running

    @pytest.mark.asyncio
    async def test_start_server_already_running(self):
        """Test starting server that's already running."""
        self.stdio_server._running = True  # Simulate already running

        # Should not raise an exception, just log a warning
        await self.stdio_server.start()
        assert self.stdio_server._running is True

    def test_start_unsupported_transport(self):
        """Test starting server with unsupported transport."""
        invalid_server = MCPServer("invalid_server", "websocket")  # Not implemented

        with pytest.raises(ValueError, match="Unknown transport: websocket"):
            asyncio.run(invalid_server.start())

    @pytest.mark.asyncio
    async def test_stop_server_not_running(self):
        """Test stopping server that's not running."""
        # Should not raise an exception
        await self.stdio_server.stop()
        assert not self.stdio_server._running

    @pytest.mark.asyncio
    async def test_stop_server_cleans_up_state(self):
        """Test that stopping server cleans up internal state."""
        # Simulate running server
        self.sse_server._running = True
        self.sse_server._app = Mock()
        self.sse_server._server_task = Mock()
        self.sse_server._server_task.cancel = Mock()

        # Mock the task to avoid actual cancellation
        async def mock_task():
            raise asyncio.CancelledError()

        self.sse_server._server_task = asyncio.create_task(mock_task())

        await self.sse_server.stop()

        assert not self.sse_server._running
        assert self.sse_server._app is None
        assert self.sse_server._server_task is None

    def test_server_repr(self):
        """Test string representation of server."""
        repr_str = repr(self.stdio_server)

        assert "MCPServer" in repr_str
        assert "test_stdio_server" in repr_str
        assert "stdio" in repr_str
        assert "running=False" in repr_str

    def test_server_repr_running(self):
        """Test string representation when server is running."""
        self.sse_server._running = True
        repr_str = repr(self.sse_server)

        assert "running=True" in repr_str

    @patch('src.lib.system_services.mcp_server.FastMCP')
    def test_mcp_instance_created(self, mock_fastmcp):
        """Test that FastMCP instance is created properly."""
        mock_fastmcp.return_value = Mock()

        server = MCPServer("test_server", "stdio")

        mock_fastmcp.assert_called_once_with(name="test_server")
        assert server.mcp is not None
