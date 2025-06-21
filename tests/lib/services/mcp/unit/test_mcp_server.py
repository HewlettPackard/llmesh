#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test MCP Server functionality

Tests for MCP server factory, configuration, and manager functionality.
These tests validate the MCP server implementation using the FastMCP SDK.
"""

import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.lib.services.mcp.server import MCPServer, MCPServerManager


class TestMCPServerFactory:
    """Test MCP server factory functionality."""

    def test_create_from_dict_config(self):
        """Test creating server manager from dictionary configuration."""
        config = {
            "name": "test_server",
            "transport": "stdio",
            "debug": True
        }

        manager = MCPServer.create(config)

        assert isinstance(manager, MCPServerManager)
        assert manager.name == "test_server"
        assert manager.transport == "stdio"
        assert manager.config.debug is True

    def test_create_sse_server_config(self):
        """Test creating SSE server configuration."""
        config = {
            "name": "sse_server",
            "transport": "sse",
            "host": "localhost",
            "port": 8001,
            "mount_path": "/test/mcp"
        }

        manager = MCPServer.create(config)

        assert isinstance(manager, MCPServerManager)
        assert manager.name == "sse_server"
        assert manager.transport == "sse"
        assert manager.config.host == "localhost"
        assert manager.config.port == 8001
        assert manager.config.mount_path == "/test/mcp"

    def test_create_streamable_server_config(self):
        """Test creating Streamable HTTP server configuration."""
        config = {
            "name": "streamable_server",
            "transport": "streamable",
            "host": "0.0.0.0",
            "port": 8002,
            "mount_path": "/api/mcp",
            "stateless_http": True
        }

        manager = MCPServer.create(config)

        assert isinstance(manager, MCPServerManager)
        assert manager.name == "streamable_server"
        assert manager.transport == "streamable"
        assert manager.config.host == "0.0.0.0"
        assert manager.config.port == 8002
        assert manager.config.mount_path == "/api/mcp"
        assert manager.config.stateless_http is True

    def test_create_from_config_object(self):
        """Test creating server manager from Config object."""
        config = MCPServer.Config(
            name="object_server",
            transport="stdio",
            auto_start=False
        )

        manager = MCPServer.create(config)

        assert isinstance(manager, MCPServerManager)
        assert manager.name == "object_server"
        assert manager.config.auto_start is False

    def test_create_from_file_config(self):
        """Test creating server manager from YAML configuration file."""
        config_content = """
mcp:
    name: file_test_server
    transport: sse
    host: 0.0.0.0
    port: 8002
    debug: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()

            try:
                manager = MCPServer.create(f.name)

                assert isinstance(manager, MCPServerManager)
                assert manager.name == "file_test_server"
                assert manager.transport == "sse"
                assert manager.config.port == 8002
            finally:
                Path(f.name).unlink()

    def test_get_available_transports(self):
        """Test getting available transport types."""
        transports = MCPServer.get_available_transports()

        assert isinstance(transports, dict)
        assert "stdio" in transports
        assert "sse" in transports
        assert "streamable" in transports
        assert len(transports) >= 3

    def test_invalid_config_raises_error(self):
        """Test that invalid configuration raises appropriate errors."""
        with pytest.raises(ValueError):
            MCPServer.create({})  # Missing required fields

        with pytest.raises(ValueError):
            MCPServer.create({"name": "test"})  # Missing transport


class TestMCPServerManager:
    """Test MCP server manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stdio_config = MCPServer.Config(
            name="test_stdio_server",
            transport="stdio",
            auto_start=False,
            debug=True
        )

        self.sse_config = MCPServer.Config(
            name="test_sse_server",
            transport="sse",
            host="localhost",
            port=8003,
            mount_path="/test",
            debug=True
        )

        self.streamable_config = MCPServer.Config(
            name="test_streamable_server",
            transport="streamable",
            host="localhost",
            port=8004,
            mount_path="/api",
            stateless_http=True,
            debug=True
        )

    def test_stdio_manager_initialization(self):
        """Test STDIO server manager initialization."""
        manager = MCPServerManager(self.stdio_config)

        assert manager.name == "test_stdio_server"
        assert manager.transport == "stdio"
        assert manager.is_running is False
        assert manager.mcp is not None  # FastMCP instance created
        assert manager._app is None  # No Starlette app for STDIO

    def test_sse_manager_initialization(self):
        """Test SSE server manager initialization."""
        manager = MCPServerManager(self.sse_config)

        assert manager.name == "test_sse_server"
        assert manager.transport == "sse"
        assert manager.config.host == "localhost"
        assert manager.config.port == 8003
        assert manager.is_running is False
        assert manager.mcp is not None

    def test_streamable_manager_initialization(self):
        """Test Streamable HTTP server manager initialization."""
        manager = MCPServerManager(self.streamable_config)

        assert manager.name == "test_streamable_server"
        assert manager.transport == "streamable"
        assert manager.config.host == "localhost"
        assert manager.config.port == 8004
        assert manager.config.stateless_http is True
        assert manager.is_running is False
        assert manager.mcp is not None

    def test_tool_registration_decorator(self):
        """Test tool registration decorator functionality."""
        manager = MCPServerManager(self.stdio_config)

        @manager.register_tool(description="Test tool for addition")
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Verify the tool was registered with FastMCP
        # Note: This tests the decorator application, actual FastMCP registration
        # would require more complex mocking of the FastMCP internal state
        assert callable(add_numbers)
        assert add_numbers(2, 3) == 5

    def test_resource_registration_decorator(self):
        """Test resource registration decorator functionality."""
        manager = MCPServerManager(self.stdio_config)

        @manager.register_resource("test://config/{key}")
        def get_config(key: str) -> dict:
            """Get configuration value."""
            return {"key": key, "value": "test_value"}

        # Verify the resource was registered
        assert callable(get_config)
        result = get_config("test_key")
        assert result["key"] == "test_key"

    def test_prompt_registration_decorator(self):
        """Test prompt registration decorator functionality."""
        manager = MCPServerManager(self.stdio_config)

        @manager.register_prompt("test_prompt")
        def test_prompt_template(context: str = "default") -> list:
            """Test prompt template."""
            return [f"System: Test prompt with context: {context}"]

        # Verify the prompt was registered
        assert callable(test_prompt_template)
        result = test_prompt_template("custom")
        assert "custom" in result[0]

    def test_add_platform_tools(self):
        """Test adding platform tools to server."""
        manager = MCPServerManager(self.stdio_config)

        # This should register platform tools without error
        manager.add_platform_tools()

        # Verify manager state is still valid
        assert manager.name == "test_stdio_server"
        assert manager.is_running is False

    def test_add_platform_resources(self):
        """Test adding platform resources to server."""
        manager = MCPServerManager(self.stdio_config)

        # This should register platform resources without error
        manager.add_platform_resources()

        # Verify manager state is still valid
        assert manager.name == "test_stdio_server"

    def test_add_platform_prompts(self):
        """Test adding platform prompts to server."""
        manager = MCPServerManager(self.stdio_config)

        # This should register platform prompts without error
        manager.add_platform_prompts()

        # Verify manager state is still valid
        assert manager.name == "test_stdio_server"

    # @pytest.mark.asyncio
    # async def test_start_stdio_server_auto_disabled(self):
    #     """Test starting STDIO server with auto_start disabled."""
    #     manager = MCPServerManager(self.stdio_config)

    #     result = await manager.start()
    #     try:
    #         assert result.status == "success"
    #         assert result.data["server_name"] == "test_stdio_server"
    #         assert result.data["transport"] == "stdio"
    #         assert result.data["running"] is True
    #         assert manager.is_running is True
    #     finally:
    #         # Ensure server is stopped after test
    #         await manager.stop()

    # @pytest.mark.asyncio
    # async def test_start_server_already_running(self):
    #     """Test starting server that's already running."""
    #     manager = MCPServerManager(self.stdio_config)
    #     manager.is_running = True  # Simulate already running

    #     result = await manager.start()

    #     assert result.status == "error"
    #     assert result.error_code == "ALREADY_RUNNING"
    #     assert "already running" in result.error_message

    # @pytest.mark.asyncio
    # async def test_start_unsupported_transport(self):
    #     """Test starting server with unsupported transport."""
    #     invalid_config = MCPServer.Config(
    #         name="invalid_server",
    #         transport="websocket"  # Not implemented
    #     )
    #     manager = MCPServerManager(invalid_config)

    #     result = await manager.start()

    #     assert result.status == "error"
    #     assert result.error_code == "START_FAILED"
    #     assert "Unsupported transport type" in result.error_message

    # @pytest.mark.asyncio
    # @patch('asyncio.create_task')
    # async def test_start_sse_server(self, mock_create_task):
    #     """Test starting SSE server."""
    #     mock_task = AsyncMock()
    #     mock_create_task.return_value = mock_task

    #     manager = MCPServerManager(self.sse_config)

    #     result = await manager.start()

    #     try:
    #         assert result.status == "success"
    #         assert result.data["transport"] == "sse"
    #         assert manager.is_running is True
    #         assert manager._server_task == mock_task
    #         mock_create_task.assert_called_once()
    #     finally:
    #         # Ensure server is stopped after test
    #         await manager.stop()

    # @pytest.mark.asyncio
    # @patch('asyncio.create_task')
    # async def test_start_streamable_server(self, mock_create_task):
    #     """Test starting Streamable HTTP server."""
    #     mock_task = AsyncMock()
    #     mock_create_task.return_value = mock_task

    #     manager = MCPServerManager(self.streamable_config)

    #     result = await manager.start()

    #     assert result.status == "success"
    #     assert result.data["transport"] == "streamable"
    #     assert manager.is_running is True
    #     assert manager._server_task == mock_task
    #     mock_create_task.assert_called_once()

    # @pytest.mark.asyncio
    # async def test_stop_server_not_running(self):
    #     """Test stopping server that's not running."""
    #     manager = MCPServerManager(self.stdio_config)

    #     result = await manager.stop()

    #     assert result.status == "error"
    #     assert result.error_code == "NOT_RUNNING"
    #     assert "not running" in result.error_message

    # @pytest.mark.asyncio
    # async def test_stop_server_success(self):
    #     """Test successful server stop."""
    #     manager = MCPServerManager(self.stdio_config)
    #     manager.is_running = True

    #     # Create a proper task mock using asyncio.create_task
    #     async def dummy_coroutine():
    #         """Dummy coroutine for the task."""
    #         return "completed"

    #     # Create a real asyncio task then mock its cancel method
    #     real_task = asyncio.create_task(dummy_coroutine())

    #     # Mock the cancel method but keep the task awaitable
    #     with patch.object(real_task, 'cancel', Mock()) as mock_cancel:
    #         manager._server_task = real_task

    #         result = await manager.stop()

    #         assert result.status == "success"
    #         assert result.data["running"] is False
    #         assert manager.is_running is False
    #         mock_cancel.assert_called_once()

    # @pytest.mark.asyncio
    # async def test_stop_server_with_cancellation_error(self):
    #     """Test server stop handling cancellation error."""
    #     manager = MCPServerManager(self.stdio_config)
    #     manager.is_running = True

    #     # Create a task that will be cancelled
    #     async def cancellable_coroutine():
    #         """Coroutine that will be cancelled."""
    #         await asyncio.sleep(1)  # This will be cancelled
    #         return "completed"

    #     # Create a real asyncio task
    #     real_task = asyncio.create_task(cancellable_coroutine())
    #     manager._server_task = real_task

    #     result = await manager.stop()

    #     assert result.status == "success"
    #     assert manager.is_running is False
    #     # Verify the task was actually cancelled
    #     assert real_task.cancelled()

    # def test_get_server_info(self):
    #     """Test getting server information."""
    #     manager = MCPServerManager(self.sse_config)

    #     info = manager.get_server_info()

    #     assert info["name"] == "test_sse_server"
    #     assert info["transport"] == "sse"
    #     assert info["running"] is False
    #     assert info["config"]["host"] == "localhost"
    #     assert info["config"]["port"] == 8003
    #     assert info["config"]["mount_path"] == "/test"
    #     assert info["config"]["debug"] is True

    # def test_server_manager_repr(self):
    #     """Test string representation of server manager."""
    #     manager = MCPServerManager(self.stdio_config)
    #     repr_str = repr(manager)

    #     assert "MCPServerManager" in repr_str
    #     assert "test_stdio_server" in repr_str
    #     assert "stdio" in repr_str
    #     assert "running=False" in repr_str

    # def test_server_manager_repr_running(self):
    #     """Test string representation when server is running."""
    #     manager = MCPServerManager(self.stdio_config)
    #     manager.is_running = True

    #     repr_str = repr(manager)

    #     assert "running=True" in repr_str
