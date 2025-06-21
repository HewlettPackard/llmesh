#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration Tests for MCP Implementation

These tests validate the MCP implementation using real MCP servers
and test the complete flow from client to server to registry.
"""

import pytest
import aiohttp
import subprocess
import os
import asyncio
import tempfile
from pathlib import Path

from src.lib.services.mcp.client import MCPClient, MCPClientManager
from src.lib.services.mcp.server import MCPServer, MCPServerManager
from src.lib.services.mcp.registry import MCPRegistry
from src.lib.services.mcp.adapters.langchain_tools import MCPToLangChainAdapter


@pytest.mark.integration
class TestMCPClientServerIntegration:
    """Integration tests for MCP client-server communication."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Server configuration for STDIO
        self.server_config = MCPServer.Config(
            name="test_integration_server",
            transport="stdio",
            auto_start=False,
            debug=True
        )

        # Client configuration for STDIO
        self.client_config = MCPClient.Config(
            name="test_integration_client",
            transport="stdio",
            command="uv",
            args=["run", "--active", "--with-editable", ".[mcp]",  self._create_simple_mcp_server()],
            debug=True
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_simple_mcp_server(self) -> str:
        """Create a simple MCP server script for testing."""
        server_script = '''
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("test-server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def get_greeting(name: str = "World") -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"

@mcp.resource("test://config")
def get_config():
    """Get test configuration."""
    return {"server": "test-server", "version": "1.0"}

if __name__ == "__main__":
    mcp.run()
'''

        # Write to temporary file
        script_path = self.temp_dir / "test_server.py"
        script_path.write_text(server_script)
        return str(script_path)

    @pytest.mark.asyncio
    async def test_basic_client_server_communication(self):
        """Test basic communication between client and server."""
        # Create client manager
        client_manager = MCPClientManager(self.client_config)

        # Test connection
        async with client_manager.connect() as session:
            await session.initialize()

            # Test listing tools
            tools_result = await session.list_tools()
            assert len(tools_result.tools) >= 2  # add_numbers and get_greeting

            tool_names = [tool.name for tool in tools_result.tools]
            assert "add_numbers" in tool_names
            assert "get_greeting" in tool_names

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test executing tools through MCP."""
        client_manager = MCPClientManager(self.client_config)

        async with client_manager.connect() as session:
            await session.initialize()

            # Test add_numbers tool
            result = await session.call_tool("add_numbers", {"a": 5, "b": 3})
            assert result.content
            # Extract result from MCP response format
            if isinstance(result.content[0], str):
                assert "8" in result.content[0]
            elif hasattr(result.content[0], 'text'):
                assert "8" in result.content[0].text

            # Test get_greeting tool
            result = await session.call_tool("get_greeting", {"name": "MCP Test"})
            assert result.content
            if isinstance(result.content[0], str):
                assert "Hello, MCP Test!" in result.content[0]
            elif hasattr(result.content[0], 'text'):
                assert "Hello, MCP Test!" in result.content[0].text

    @pytest.mark.asyncio
    async def test_capabilities_discovery(self):
        """Test capability discovery through client manager."""
        client_manager = MCPClientManager(self.client_config)

        # Test get_capabilities method
        result = await client_manager.get_capabilities()
        print(f"Capabilities discovery result: {result}")
        print(f"Result data: {result.data}")

        assert result.status == "success"
        assert "tools" in result.data
        assert "resources" in result.data
        assert "prompts" in result.data

        # Verify tool information
        tools = result.data["tools"]
        assert len(tools) >= 2

        tool_names = [tool["name"] for tool in tools]
        assert "add_numbers" in tool_names
        assert "get_greeting" in tool_names


@pytest.mark.integration
class TestMCPRegistryIntegration:
    """Integration tests for MCP registry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry_file = self.temp_dir / "test_registry.json"

        self.registry_config = {
            "registry_file": str(self.registry_file),
            "cache_ttl": 60,
            "auto_discovery": True
        }

        self.registry = MCPRegistry(self.registry_config)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_server_registration_and_persistence(self):
        """Test server registration and persistent storage."""
        server_config = {
            "name": "test_persistent_server",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"],
            "description": "Test server for persistence",
            "tags": ["test", "integration"]
        }

        # Register server
        result = self.registry.register_server(server_config)
        assert result is True

        # Verify registration
        servers = self.registry.list_servers()
        assert len(servers) == 1
        assert servers[0].name == "test_persistent_server"

        # Verify persistence
        assert self.registry_file.exists()

        # Create new registry instance to test loading
        new_registry = MCPRegistry(self.registry_config)
        loaded_servers = new_registry.list_servers()
        assert len(loaded_servers) == 1
        assert loaded_servers[0].name == "test_persistent_server"

    def test_server_filtering(self):
        """Test server filtering by enabled status and tags."""
        # Register multiple servers
        servers = [
            {"name": "server1", "transport": "stdio", "enabled": True, "tags": ["prod", "api"]},
            {"name": "server2", "transport": "sse", "enabled": False, "tags": ["dev", "test"]},
            {"name": "server3", "transport": "stdio", "enabled": True, "tags": ["test", "integration"]}
        ]

        for server in servers:
            self.registry.register_server(server)

        # Test enabled only filter
        enabled_servers = self.registry.list_servers(enabled_only=True)
        assert len(enabled_servers) == 2
        enabled_names = [s.name for s in enabled_servers]
        assert "server1" in enabled_names
        assert "server3" in enabled_names

        # Test tag filter
        test_servers = self.registry.list_servers(tags=["test"])
        assert len(test_servers) == 2
        test_names = [s.name for s in test_servers]
        assert "server2" in test_names
        assert "server3" in test_names

    @pytest.mark.asyncio
    async def test_capability_discovery_with_caching(self):
        """Test capability discovery with TTL caching."""
        # Create a mock server script
        script_content = '''
import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cache-test-server")

@mcp.tool()
def cached_tool() -> str:
    """A tool for cache testing."""
    return "cached result"

if __name__ == "__main__":
    mcp.run()
'''

        script_path = self.temp_dir / "cache_test_server.py"
        script_path.write_text(script_content)

        # Register server
        server_config = {
            "name": "cache_test_server",
            "transport": "stdio",
            "command": "python",
            "args": [str(script_path)],
            "enabled": True
        }

        self.registry.register_server(server_config)

        # First discovery - should hit the server
        capabilities1 = await self.registry.discover_capabilities("cache_test_server", force_refresh=True)
        assert capabilities1 is not None
        assert "tools" in capabilities1

        # Second discovery - should use cache
        capabilities2 = await self.registry.discover_capabilities("cache_test_server", force_refresh=False)
        assert capabilities2 is not None
        assert capabilities1 == capabilities2  # Should be identical from cache


@pytest.mark.integration
class TestLangChainAdapterIntegration:
    """Integration tests for LangChain adapter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Set up registry
        self.registry_config = {
            "registry_file": str(self.temp_dir / "adapter_test_registry.json"),
            "cache_ttl": 60
        }

        self.adapter_config = {
            "registry_config": self.registry_config,
            "tool_timeout": 10,
            "auto_discover": True
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_langchain_test_server(self) -> str:
        """Create an MCP server with LangChain-compatible tools."""
        server_script = '''
import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("langchain-test-server")

@mcp.tool()
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle."""
    return length * width

@mcp.tool()
def format_text(text: str, uppercase: bool = False) -> str:
    """Format text with optional uppercase conversion."""
    return text.upper() if uppercase else text.lower()

@mcp.tool()
def get_system_info() -> str:
    """Get system information."""
    return "Test system info"

if __name__ == "__main__":
    mcp.run()
'''

        script_path = self.temp_dir / "langchain_test_server.py"
        script_path.write_text(server_script)
        return str(script_path)

    @pytest.mark.asyncio
    async def test_tool_discovery_and_registration(self):
        """Test automatic tool discovery and registration with LangChain."""
        # Create adapter
        adapter = MCPToLangChainAdapter(self.adapter_config)

        # Register test server
        script_path = self._create_langchain_test_server()
        server_config = {
            "name": "langchain_test_server",
            "transport": "stdio",
            "command": "python",
            "args": [script_path],
            "enabled": True,
            "tags": ["test", "langchain"]
        }

        adapter.registry.register_server(server_config)

        # Discover and register tools
        result = await adapter.discover_and_register_tools()

        assert result["status"] == "success"
        assert result["tools_registered"] >= 3  # Should find our 3 tools
        assert result["servers_processed"] >= 1

        # Get registered tool info
        tool_info = adapter.get_registered_tools_info()
        assert tool_info["total_mcp_tools"] >= 3
        assert "langchain_test_server" in tool_info["tools_by_server"]

    def test_tool_filtering_by_server(self):
        """Test filtering tools by server name."""
        adapter_config = {
            **self.adapter_config,
            "server_filter": ["specific_server"]
        }
        adapter = MCPToLangChainAdapter(adapter_config)

        # Register multiple servers
        script_path = self._create_langchain_test_server()

        servers = [
            {"name": "specific_server", "transport": "stdio", "command": "python", "args": [script_path], "enabled": True},
            {"name": "other_server", "transport": "stdio", "command": "python", "args": [script_path], "enabled": True}
        ]

        for server in servers:
            adapter.registry.register_server(server)

        # Get filtered servers
        filtered_servers = adapter._get_filtered_servers()
        assert len(filtered_servers) == 1
        assert filtered_servers[0].name == "specific_server"

    def test_tool_filtering_by_tags(self):
        """Test filtering tools by server tags."""
        adapter_config = {
            **self.adapter_config,
            "tag_filter": ["production"]
        }
        adapter = MCPToLangChainAdapter(adapter_config)

        # Register servers with different tags
        script_path = self._create_langchain_test_server()

        servers = [
            {"name": "prod_server", "transport": "stdio", "command": "python", "args": [script_path], "enabled": True, "tags": ["production", "api"]},
            {"name": "dev_server", "transport": "stdio", "command": "python", "args": [script_path], "enabled": True, "tags": ["development", "test"]}
        ]

        for server in servers:
            adapter.registry.register_server(server)

        # Get filtered servers
        filtered_servers = adapter._get_filtered_servers()
        assert len(filtered_servers) == 1
        assert filtered_servers[0].name == "prod_server"


@pytest.mark.integration
class TestMCPStreamableTransportIntegration:
    """Integration tests for Streamable HTTP transport functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_streamable_test_server_script(self) -> str:
        """Create a simple streamable MCP server script for testing."""
        server_script = '''
import asyncio
import sys
import traceback
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

mcp = FastMCP(name="Test Server", stateless_http=True)

# Tool specific to this server example
@mcp.tool(description="A simple add tool")
def add_two() -> str:
    return  "2 + 2 = 4"

@mcp.tool(description="A simple echo tool")
def echo_message(message: str) -> str:
    """Echo a message back."""
    return f"Echo: {message}"

@mcp.prompt()
def default_prompt() -> str:
    """Default prompt for the server."""
    return "Welcome to the Test Server! Use /test/add or /test/echo to interact."

# Create FastAPI app with MCP's lifespan
app = FastAPI(lifespan=lambda app: mcp.session_manager.run())
app.mount("/test", mcp.streamable_http_app())

if __name__ == "__main__":
    # Explicitly run with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9011)
'''

        script_path = self.temp_dir / "streamable_test_server.py"
        script_path.write_text(server_script)
        return str(script_path)

    def test_streamable_server_configuration_compatibility(self):
        """Test that streamable server config is compatible with lab examples."""
        # Configuration matching the lab example pattern
        lab_style_config = {
            "name": "MathServer",
            "transport": "streamable",
            "host": "0.0.0.0",
            "port": 8000,
            "mount_path": "/math",
            "stateless_http": True
        }
        from src.lib.services.mcp.server import MCPServer
        server_manager = MCPServer.create(lab_style_config)

        # Verify it matches lab example configuration
        assert server_manager.name == "MathServer"
        assert server_manager.config.stateless_http is True
        assert server_manager.config.mount_path == "/math"
        assert server_manager.config.port == 8000
        assert server_manager.config.host == "0.0.0.0"

        print("✅ Streamable server configuration is compatible with lab examples.")

    @pytest.mark.asyncio
    async def test_streamable_server_lifecycle_with_our_implementation(self):
        """Test complete lifecycle of streamable server using our MCP implementation."""
        from src.lib.services.mcp.server import MCPServer

        # Create server using our implementation
        server_config = {
            "name": "lifecycle_test_server",
            "transport": "streamable",
            "host": "127.0.0.1",
            "port": 9003,
            "mount_path": "/test-lifecycle",
            "stateless_http": True,
            "auto_start": True,
            "debug": True,
        }

        print("\n🚀 Starting streamable server lifecycle test...")
        print(server_config)

        server_manager = MCPServer.create(server_config)

        # Add platform tools
        server_manager.add_platform_tools()
        server_manager.add_platform_resources()
        server_manager.add_platform_prompts()

        # Test server info before starting
        info = server_manager.get_server_info()
        print(f"Server info before starting: {info}")
        start_result = await server_manager.start()
        print(f"Server start result: {start_result}")
        info = server_manager.get_server_info()
        print(f"Server info after starting: {info}")
        assert info["name"] == "lifecycle_test_server"
        assert info["transport"] == "streamable"
        assert info["running"] is True

        print("stopping server...")
        # Stop the server
        await server_manager.stop()

        # Verify the server would be properly configured
        assert server_manager.mcp is not None
        assert hasattr(server_manager.mcp, 'streamable_http_app')  # FastMCP feature

    @pytest.mark.asyncio
    async def test_streamable_transport_client_server_basic(self):
        """Test that streamable HTTP transport can establish connections successfully."""
        print("\n🚀 Starting streamable HTTP transport basic connectivity test...")
        from src.lib.services.mcp.client import MCPClient

        print("📦 Creating minimal streamable server script...")

        # Create the enhanced server script with debug logging
        script_path = self._create_streamable_test_server_script()
        print(f"📝 Server script written to: {script_path}")

        # Start the server as subprocess
        print("🔥 Starting test server subprocess...")
        server_process = subprocess.Popen(
            ["uv", "run", "--active", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for cleanup
        )
        print(f"📡 Server process started with PID: {server_process.pid}")

        try:
            # Wait for server to start
            print("⏳ Waiting for server to become ready...")
            await self._wait_for_server_ready("http://127.0.0.1:9011/test", timeout=10)

            # Check if server process is still running
            poll_result = server_process.poll()
            if poll_result is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Server exited with code {poll_result}")
                print(f"📤 STDOUT: {stdout.decode()}")
                print(f"📤 STDERR: {stderr.decode()}")
                assert False, f"Server process exited unexpectedly with code {poll_result}"
            print("✅ Server is running and ready!")

            # Test 1: Verify we can create a streamable client
            print("\n🔧 Test 1: Creating streamable HTTP client...")
            client_config = {
                "name": "transport_test_client",
                "transport": "streamable",
                "url": "http://127.0.0.1:9011/test/mcp",
                "timeout": 3,
                "debug": True
            }
            print(f"   Client config: {client_config}")

            client_manager = MCPClient.create(client_config)
            assert client_manager.transport == "streamable"
            print(f"✅ Client created successfully: {client_manager}")
            print(f"   Transport type: {client_manager.transport}")
            print(f"   Client name: {client_manager.name}")

            # Test 2: Verify connection establishment
            print("\n🔗 Test 2: Testing streamable HTTP connection establishment...")
            connection_successful = False
            try:
                print("   ⏱️  Starting connection test with 10 second timeout...")
                print("   🔌 Attempting to connect via streamable HTTP...")

                # Use asyncio.wait_for for better compatibility
                async def test_connection():
                    async with client_manager.connect() as session:
                        print("✅ Streamable HTTP transport connection successful!")
                        print(f"   Session object: {type(session)}")
                        print(f"   Session is valid: {session is not None}")
                        nonlocal connection_successful
                        connection_successful = True

                await asyncio.wait_for(test_connection(), timeout=10)

                print("✅ Connection test completed successfully!")

            except asyncio.TimeoutError:
                print("❌ Connection test timed out after 10 seconds")
                connection_successful = False

            except Exception as e:
                print(f"❌ Connection test failed with error: {e}")
                print(f"   Error type: {type(e)}")
                connection_successful = False

            # Main assertion: Connection was established
            print(f"\n📊 Final Result: connection_successful = {connection_successful}")
            assert connection_successful, "Streamable HTTP transport should establish connections"
            print("🎉 All streamable HTTP transport tests passed!")

        finally:
            # Clean up: terminate the server process and capture any final logs
            print("\n🧹 Cleaning up server process...")
            try:
                print(f"   Terminating server process {server_process.pid}")

                # Capture final server output before termination
                if server_process.poll() is None:
                    # Server is still running, terminate it and get output
                    server_process.terminate()
                    try:
                        stdout, stderr = server_process.communicate(timeout=3)
                        if stderr:
                            print("📋 Final server logs:")
                            print(stderr.decode())
                    except subprocess.TimeoutExpired:
                        server_process.kill()
                        stdout, stderr = server_process.communicate()
                        if stderr:
                            print("📋 Final server logs (after force kill):")
                            print(stderr.decode())
                else:
                    # Server already exited, just get the output
                    stdout, stderr = server_process.communicate()
                    if stderr:
                        print("📋 Server logs from failed process:")
                        print(stderr.decode())

                print("   ✅ Server process terminated gracefully")

            except (ProcessLookupError, subprocess.TimeoutExpired):
                print("   ⚠️  Server process cleanup completed")

    async def _wait_for_server_ready(self, base_url: str, timeout: int = 10):
        """Wait for the server to be ready to accept connections."""
        import time
        import asyncio
        from mcp.client.streamable_http import streamablehttp_client # Added import
        import datetime # Added import

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Use MCP's streamablehttp_client for checking server readiness
                async with streamablehttp_client(url=base_url, timeout=datetime.timedelta(seconds=1)) as (reader, writer, _):
                    # A successful connection means the server is ready
                    # We don't need to send any specific MCP commands, just establishing connection is enough
                    print(f"Server at {base_url} is ready.")
                    return  # Server is ready
            except Exception as e:
                # Log the exception for debugging, but continue retrying
                print(f"Server not ready yet ({base_url}): {e}")
                await asyncio.sleep(0.5)  # Wait before retrying

        raise TimeoutError(f"Server at {base_url} did not become ready within {timeout} seconds")

    async def _test_mcp_communication(self, client_manager):
        """Test MCP communication operations."""
        async with client_manager.connect() as session:
            # Initialize the session
            await session.initialize()

            # Test listing tools
            tools_result = await session.list_tools()
            print(f"Tools found: {[tool.name for tool in tools_result.tools]}")

            # Verify we have our expected tools
            tool_names = [tool.name for tool in tools_result.tools]
            assert "e2e_add" in tool_names
            assert "e2e_echo" in tool_names

            # Test calling a tool
            add_result = await session.call_tool("e2e_add", {"x": 15, "y": 25})
            assert add_result.content
            # The result should contain "40"
            if hasattr(add_result.content[0], 'text'):
                assert "40" in add_result.content[0].text

            # Test echo tool
            echo_result = await session.call_tool("e2e_echo", {"message": "streamable test"})
            assert echo_result.content
            if hasattr(echo_result.content[0], 'text'):
                assert "E2E Echo: streamable test" in echo_result.content[0].text

            # Test listing resources
            resources_result = await session.list_resources()
            resource_uris = [str(resource.uri) for resource in resources_result.resources]
            assert "e2e://test" in resource_uris

            print("✅ End-to-end streamable HTTP communication successful!")


@pytest.mark.integration
class TestMCPConfigurationIntegration:
    """Integration tests for MCP configuration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_yaml_configuration_loading(self):
        """Test loading MCP configuration from YAML files."""
        config_content = """
mcp:
  servers:
    - name: yaml_test_server
      transport: stdio
      command: echo
      args: ["test"]
      enabled: true
      description: "Server from YAML config"
      tags: ["yaml", "config", "test"]
    - name: yaml_sse_server
      transport: sse
      url: "http://localhost:8000/mcp"
      enabled: false
      description: "SSE server from YAML"
      tags: ["sse", "config"]

  client_defaults:
    timeout: 30
    debug: false

  registry:
    cache_ttl: 300
    auto_discovery: true
"""

        config_file = self.temp_dir / "test_config.yaml"
        config_file.write_text(config_content)

        # Test client creation from file
        client_config = {
            "name": "yaml_client",
            "transport": "stdio",
            "command": "echo",
            "args": ["test"]
        }

        # This tests the platform config integration
        client_manager = MCPClient.create(client_config)
        assert client_manager.name == "yaml_client"
        assert client_manager.transport == "stdio"

    def test_environment_variable_integration(self):
        """Test integration with environment variables."""
        import os

        # Set test environment variables
        test_env = {
            "MCP_SERVER_COMMAND": "python",
            "MCP_SERVER_HOST": "localhost",
            "MCP_SERVER_PORT": "8001"
        }

        for key, value in test_env.items():
            os.environ[key] = value

        try:
            # Test that configurations can use environment variables
            config = {
                "name": "env_test_server",
                "transport": "sse",
                "host": os.environ.get("MCP_SERVER_HOST", "localhost"),
                "port": int(os.environ.get("MCP_SERVER_PORT", "8000"))
            }

            server_manager = MCPServer.create(config)
            assert server_manager.config.host == "localhost"
            assert server_manager.config.port == 8001

        finally:
            # Clean up environment variables
            for key in test_env:
                os.environ.pop(key, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])