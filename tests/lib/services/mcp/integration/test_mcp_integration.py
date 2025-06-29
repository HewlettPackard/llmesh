#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration Tests for MCP Implementation

These tests validate the MCP implementation using real MCP servers
and test the complete flow from client to server to registry.
"""

import pytest
import subprocess
import os
import asyncio
import tempfile
from pathlib import Path
import aiohttp

from src.lib.system_services.mcp_client import MCPClient
from src.lib.system_services.mcp_server import MCPServer
from src.lib.system_services.mcp_registry import MCPRegistry

@pytest.mark.integration
class TestMCPClientServerIntegration:
    """Integration tests for MCP client-server communication."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create simple MCP server script
        self.server_script = self._create_simple_mcp_server()

        # Client configuration for STDIO
        self.client = MCPClient(
            name="test_integration_client",
            transport="stdio",
            command="uv",
            args=["run", "--active", "--with-editable", ".[mcp]", self.server_script]
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
        async with self.client as client:
            # Test listing tools
            tools = await client.list_tools()
            assert len(tools) >= 2  # add_numbers and get_greeting

            tool_names = [tool["name"] for tool in tools]
            assert "add_numbers" in tool_names
            assert "get_greeting" in tool_names

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test executing tools through MCP."""
        async with self.client as client:
            # Test add_numbers tool
            result = await client.invoke_tool("add_numbers", {"a": 5, "b": 3})
            assert result
            # Extract result from MCP response format
            if isinstance(result[0], str):
                assert "8" in result[0]
            elif hasattr(result[0], 'text'):
                assert "8" in result[0].text

            # Test get_greeting tool
            result = await client.invoke_tool("get_greeting", {"name": "MCP Test"})
            assert result
            if isinstance(result[0], str):
                assert "Hello, MCP Test!" in result[0]
            elif hasattr(result[0], 'text'):
                assert "Hello, MCP Test!" in result[0].text

    @pytest.mark.asyncio
    async def test_capabilities_discovery(self):
        """Test capability discovery through client."""
        async with self.client as client:
            # Test tools discovery
            tools = await client.list_tools()
            assert len(tools) >= 2
            tool_names = [tool["name"] for tool in tools]
            assert "add_numbers" in tool_names
            assert "get_greeting" in tool_names

            # Test resources discovery
            resources = await client.list_resources()
            assert len(resources) >= 1
            resource_uris = [resource["uri"] for resource in resources]
            assert "test://config" in resource_uris

            # Test prompts discovery
            prompts = await client.list_prompts()
            assert isinstance(prompts, list)


@pytest.mark.integration
class TestMCPRegistryIntegration:
    """Integration tests for MCP registry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry = MCPRegistry()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.fixture(autouse=True)
    async def cleanup_registry(self):
        """Async fixture to clean up registry connections."""
        yield
        await self.registry.cleanup()

    @pytest.mark.asyncio
    async def test_server_registration(self):
        """Test server registration."""
        server_config = {
            "command": "echo",
            "args": ["test"]
        }

        # Register server
        result = await self.registry.register_server(
            name="test_persistent_server",
            accessibility="internal",
            hosting="local",
            config=server_config
        )
        assert result is True

        # Verify registration
        servers = self.registry.list_servers()
        assert len(servers) == 1
        assert servers[0]["name"] == "test_persistent_server"
        assert servers[0]["accessibility"] == "internal"
        assert servers[0]["hosting"] == "local"

    @pytest.mark.asyncio
    async def test_server_filtering(self):
        """Test server filtering by accessibility and hosting."""
        # Register multiple servers
        servers = [
            {"name": "server1", "accessibility": "internal", "hosting": "local", "config": {"command": "echo"}},
            {"name": "server2", "accessibility": "external", "hosting": "remote", "config": {"url": "http://test.com", "transport": "sse"}},
            {"name": "server3", "accessibility": "both", "hosting": "local", "config": {"command": "echo"}}
        ]

        for server in servers:
            await self.registry.register_server(**server)

        # Test accessibility filter
        internal_servers = self.registry.list_servers(accessibility_filter="internal")
        assert len(internal_servers) == 1
        assert internal_servers[0]["name"] == "server1"

        # Test hosting filter
        local_servers = self.registry.list_servers(hosting_filter="local")
        assert len(local_servers) == 2
        local_names = [s["name"] for s in local_servers]
        assert "server1" in local_names
        assert "server3" in local_names

    @pytest.mark.asyncio
    async def test_registry_client_creation(self):
        """Test registry can create clients for registered servers."""
        # Create a simple test server script
        script_content = '''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("registry-test-server")

@mcp.tool()
def registry_test_tool() -> str:
    """A tool to test registry functionality."""
    return "registry test result"

if __name__ == "__main__":
    mcp.run()
'''

        script_path = self.temp_dir / "registry_test_server.py"
        script_path.write_text(script_content)

        # Register server with registry
        server_config = {
            "command": "uv",
            "args": ["run", "--active", "--with-editable", ".[mcp]", str(script_path)]
        }

        await self.registry.register_server(
            name="registry_test_server",
            accessibility="internal",
            hosting="local",
            config=server_config
        )

        # Get client through registry
        client = await self.registry.get_client("registry_test_server")
        assert client is not None
        assert client.name == "registry_test_server"
        assert client.transport == "stdio"

        # Test client functionality through registry
        tools = await client.list_tools()
        tool_names = [tool["name"] for tool in tools]
        assert "registry_test_tool" in tool_names

    @pytest.mark.asyncio
    async def test_registry_tool_discovery(self):
        """Test tool discovery through registry."""
        # Create a mock server script
        script_content = '''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("discovery-test-server")

@mcp.tool()
def discovery_tool() -> str:
    """A test tool for discovery."""
    return "discovery result"

if __name__ == "__main__":
    mcp.run()
'''

        script_path = self.temp_dir / "discovery_test_server.py"
        script_path.write_text(script_content)

        # Register server
        server_config = {
            "command": "uv",
            "args": ["run", "--active", "--with-editable", ".[mcp]", str(script_path)]
        }

        await self.registry.register_server(
            name="discovery_test_server",
            accessibility="internal",
            hosting="local",
            config=server_config
        )

        # Test tool discovery through registry
        tools = await self.registry.discover_tools(accessibility_filter="internal")
        assert "discovery_test_server" in tools
        server_tools = tools["discovery_test_server"]
        assert len(server_tools) >= 1

        tool_names = [tool["name"] for tool in server_tools]
        assert "discovery_tool" in tool_names

    @pytest.mark.asyncio
    async def test_registry_tool_invocation(self):
        """Test tool invocation through registry."""
        # Create a test server script with a specific tool
        script_content = '''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("invocation-test-server")

@mcp.tool()
def multiply_numbers(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y

if __name__ == "__main__":
    mcp.run()
'''

        script_path = self.temp_dir / "invocation_test_server.py"
        script_path.write_text(script_content)

        # Register server
        server_config = {
            "command": "uv",
            "args": ["run", "--active", "--with-editable", ".[mcp]", str(script_path)]
        }

        await self.registry.register_server(
            name="invocation_test_server",
            accessibility="internal",
            hosting="local",
            config=server_config
        )

        # Test tool invocation through registry
        result = await self.registry.invoke_tool(
            "invocation_test_server",
            "multiply_numbers",
            {"x": 6, "y": 7}
        )

        assert result
        # Check if result contains expected value
        if isinstance(result[0], str):
            assert "42" in result[0]
        elif hasattr(result[0], 'text'):
            assert "42" in result[0].text

    @pytest.mark.asyncio
    async def test_internal_server_with_setup_callback(self):
        """Test internal server creation with setup callback."""
        # Define setup callback that adds tools
        async def setup_platform_tools(server: MCPServer):
            @server.tool(description="Get platform status")
            def platform_status():
                return {"status": "healthy", "version": "1.0.0"}

            # Also test programmatic tool registration
            def get_uptime():
                return {"uptime": "24h"}

            server.register_tool("get_uptime", get_uptime, "Get system uptime")

        # Register internal server with callback
        await self.registry.register_server(
            name="platform_internal",
            accessibility="internal",
            hosting="local",
            config={
                "use_internal_server": True,
                "transport": "sse",
                "host": "localhost",
                "port": 9010,
                "setup_callback": setup_platform_tools
            }
        )

        # Start the internal server
        started = await self.registry.start_server("platform_internal")
        assert started is True

        # Verify the server entry has our MCPServer instance
        entry = self.registry.servers["platform_internal"]
        assert entry.server is not None
        assert isinstance(entry.server, MCPServer)
        assert entry.server.name == "platform_internal"

    @pytest.mark.asyncio
    async def test_stdio_transport_through_registry(self):
        """Test stdio transport integration through registry client creation."""
        # Create a simple test server script for stdio transport
        script_content = '''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("stdio-registry-server")

@mcp.tool()
def stdio_test_tool(message: str = "Hello") -> str:
    """A tool to test stdio transport through registry."""
    return f"Stdio response: {message}"

@mcp.tool()
def add_stdio_numbers(a: int, b: int) -> int:
    """Add two numbers via stdio."""
    return a + b

if __name__ == "__main__":
    mcp.run()
'''

        script_path = self.temp_dir / "stdio_registry_server.py"
        script_path.write_text(script_content)

        # Register server with stdio transport (external server)
        server_config = {
            "command": "uv",
            "args": ["run", "--active", "--with-editable", ".[mcp]", str(script_path)]
        }

        await self.registry.register_server(
            name="stdio_registry_server",
            accessibility="internal",
            hosting="local",
            config=server_config
        )

        # Get client through registry - should create stdio client
        client = await self.registry.get_client("stdio_registry_server")
        assert client is not None
        assert client.name == "stdio_registry_server"
        assert client.transport == "stdio"

        # Test tool discovery through registry
        tools = await self.registry.discover_tools(accessibility_filter="internal")
        assert "stdio_registry_server" in tools
        server_tools = tools["stdio_registry_server"]

        tool_names = [tool["name"] for tool in server_tools]
        assert "stdio_test_tool" in tool_names
        assert "add_stdio_numbers" in tool_names

        # Test tool invocation through registry
        result = await self.registry.invoke_tool(
            "stdio_registry_server",
            "stdio_test_tool",
            {"message": "Registry Test"}
        )

        assert result
        # Check if result contains expected value
        if isinstance(result[0], str):
            assert "Stdio response: Registry Test" in result[0]
        elif hasattr(result[0], 'text'):
            assert "Stdio response: Registry Test" in result[0].text

        # Test numeric tool
        result = await self.registry.invoke_tool(
            "stdio_registry_server",
            "add_stdio_numbers",
            {"a": 15, "b": 27}
        )

        assert result
        if isinstance(result[0], str):
            assert "42" in result[0]
        elif hasattr(result[0], 'text'):
            assert "42" in result[0].text


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
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    mcp = FastMCP(name="Test Server", stateless_http=True)

    @mcp.tool(description="A simple add tool")
    def add_two() -> str:
        return "2 + 2 = 4"

    @mcp.tool(description="A simple echo tool")
    def echo_message(message: str) -> str:
        """Echo a message back."""
        return f"Echo: {message}"

    # Create FastAPI app
    app = FastAPI(lifespan=lambda app: mcp.session_manager.run())
    app.mount("/test", mcp.streamable_http_app())

    @app.get("/test")
    async def health_check():
        return {"status": "healthy"}

    if __name__ == "__main__":
        logger.info("Starting streamable server on port 9011...")
        uvicorn.run(app, host="0.0.0.0", port=9011, log_level="info")

except Exception as e:
    logger.error(f"Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    raise
'''

        script_path = self.temp_dir / "streamable_test_server.py"
        script_path.write_text(server_script)
        return str(script_path)

    def test_streamable_server_initialization(self):
        """Test that streamable server can be initialized."""
        server = MCPServer("MathServer", "streamable")

        assert server.name == "MathServer"
        assert server.transport == "streamable"
        assert server.mcp is not None
        assert not server._running

    @pytest.mark.asyncio
    async def test_streamable_server_lifecycle(self):
        """Test complete lifecycle of streamable server."""
        server = MCPServer("lifecycle_test_server", "streamable")

        # Add a simple tool for testing
        @server.tool(description="Test tool")
        def test_tool() -> str:
            return "test result"

        # Verify server is not running initially
        assert not server._running

        # Test that we can call start/stop without errors
        # Note: We don't actually start the server to avoid port conflicts
        await server.stop()  # Should not raise error

        # Verify FastMCP features are available
        assert server.mcp is not None
        assert hasattr(server.mcp, 'streamable_http_app')  # FastMCP feature

    @pytest.mark.asyncio
    async def test_streamable_transport_through_registry(self):
        """Test streamable transport registration and usage through registry."""
        registry = MCPRegistry()

        try:
            # Register a streamable server
            await registry.register_server(
                name="streamable_test",
                accessibility="external",
                hosting="local",
                config={
                    "use_internal_server": True,
                    "transport": "streamable",
                    "host": "localhost",
                    "port": 9012,
                    "setup_callback": self._setup_streamable_tools
                }
            )

            # Verify registration
            servers = registry.list_servers()
            assert len(servers) == 1
            assert servers[0]["name"] == "streamable_test"

            # Start the server (would create HTTP server in real scenario)
            started = await registry.start_server("streamable_test")
            assert started is True

            # Verify server instance was created
            entry = registry.servers["streamable_test"]
            assert entry.server is not None
            assert entry.server.transport == "streamable"

        finally:
            await registry.cleanup()

    async def _setup_streamable_tools(self, server: MCPServer):
        """Setup callback for streamable server tools."""
        @server.tool(description="HTTP test tool")
        def http_test_tool():
            return {"message": "HTTP transport working"}

    @pytest.mark.asyncio
    async def test_streamable_transport_client_server_basic(self):
        """Test that streamable HTTP transport can establish connections successfully."""
        # Create the server script
        script_path = self._create_streamable_test_server_script()

        # Start the server as subprocess
        server_process = subprocess.Popen(
            ["uv", "run", "--active", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for cleanup
        )

        try:
            # Wait for server to start
            await self._wait_for_server_ready("http://127.0.0.1:9011/test", timeout=10)

            # Check if server process is still running
            poll_result = server_process.poll()
            if poll_result is not None:
                stdout, stderr = server_process.communicate()
                print(f"Server stdout: {stdout.decode() if stdout else 'None'}")
                print(f"Server stderr: {stderr.decode() if stderr else 'None'}")
                assert False, f"Server process exited unexpectedly with code {poll_result}"

            # Test streamable client creation and connection
            client = MCPClient(
                name="transport_test_client",
                transport="streamable",
                url="http://127.0.0.1:9011/test/mcp",
                timeout=3
            )

            assert client.transport == "streamable"

            # Test connection establishment
            connection_successful = False
            try:
                async with client:
                    # Test basic tool listing to verify connection works
                    tools = await client.list_tools()
                    connection_successful = True

            except Exception as e:
                print(f"Connection test failed with error: {e}")
                connection_successful = False

            # Main assertion: Connection was established
            assert connection_successful, "Streamable HTTP transport should establish connections"

        finally:
            # Clean up server process
            try:
                if server_process.poll() is None:
                    server_process.terminate()
                    try:
                        server_process.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        server_process.kill()
                        server_process.communicate()
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass

    async def _wait_for_server_ready(self, base_url: str, timeout: int = 10):
        """Wait for the server to be ready to accept connections."""
        import time

        start_time = time.time()
        last_error = None

        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, timeout=1) as response:
                        if response.status == 200:
                            return  # Server is ready
            except Exception as e:
                last_error = e
                await asyncio.sleep(0.5)  # Wait before retrying

        raise TimeoutError(f"Server at {base_url} did not become ready within {timeout} seconds. Last error: {last_error}")


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

    def test_client_configuration(self):
        """Test client configuration."""
        client = MCPClient(
            name="yaml_client",
            transport="stdio",
            command="echo",
            args=["test"]
        )

        assert client.name == "yaml_client"
        assert client.transport == "stdio"
        assert client.connection_params["command"] == "echo"
        assert client.connection_params["args"] == ["test"]

    def test_server_configuration(self):
        """Test server configuration."""
        server = MCPServer("test_server", "sse")

        assert server.name == "test_server"
        assert server.transport == "sse"
        assert server.mcp is not None

    def test_registry_initialization(self):
        """Test registry initialization patterns."""
        # Test registry without config file
        registry1 = MCPRegistry()
        assert registry1.servers == {}
        assert registry1.config == {}

        # Test registry with non-existent config file
        registry2 = MCPRegistry("/nonexistent/config.yaml")
        assert registry2.servers == {}

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
            client = MCPClient(
                name="env_test_client",
                transport="stdio",
                command=os.environ.get("MCP_SERVER_COMMAND", "python"),
                args=["test"]
            )

            assert client.connection_params["command"] == "python"

            # Test registry with environment-based config
            registry = MCPRegistry()

            # Test that registry can use env vars in server configs
            server_config = {
                "command": os.environ.get("MCP_SERVER_COMMAND", "python"),
                "args": ["--version"]
            }

            # This should work without errors
            asyncio.run(registry.register_server(
                name="env_server",
                accessibility="internal",
                hosting="local",
                config=server_config
            ))

            servers = registry.list_servers()
            assert len(servers) == 1
            assert servers[0]["name"] == "env_server"

        finally:
            # Clean up environment variables
            for key in test_env:
                os.environ.pop(key, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
