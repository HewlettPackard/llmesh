#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Client module for connecting to Model Context Protocol servers within LATMesh.

This module provides the MCPClient class, a simplified wrapper around the MCP SDK
that enables connections to MCP servers using various transport protocols including
stdio, sse, and streamable HTTP transports.

Example:
    Basic usage:

    .. code-block:: python

        from src.lib.system_services.mcp_client import MCPClient

        # Create stdio client
        client = MCPClient(
            name="my_server",
            transport="stdio",
            command="python",
            args=["server.py"]
        )

        # Use as context manager
        async with client:
            tools = await client.list_tools()
            result = await client.invoke_tool("my_tool", {"arg": "value"})
"""
import datetime
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from src.lib.core.log import Logger
from src.lib.system_services.mcp_auth import OAuthClient

logger = Logger().get_logger()


class MCPClient:
    """
    Client for connecting to Model Context Protocol (MCP) servers.

    This class provides a simplified interface for connecting to MCP servers using
    various transport protocols. It automatically handles connection management,
    session initialization, and provides convenient methods for tool discovery
    and invocation.

    Attributes:
        name (str): The client name used for logging and identification.
        transport (str): The transport protocol ("stdio", "sse", or "streamable").
        connection_params (dict): Transport-specific connection parameters.
        logger: Logger instance for debugging and error reporting.
    """

    def __init__(
    self,
    name: str,
    transport: str,
    auth_config: Optional[Dict[str, Any]] = None,
    **connection_params
):
        """
        Initialize MCP client with transport-specific configuration.

        :param name: Unique client identifier used for logging and debugging.
        :type name: str
        :param transport: Transport protocol to use for server communication.
            Valid options are "stdio", "sse", or "streamable".
        :type transport: str
        **STDIO Transport Parameters:**

        :param command: Executable command to launch the MCP server.
        :type command: str
        :param args: Command-line arguments for the server process.
        :type args: list[str], optional
        :param env: Environment variables for the server process.
        :type env: dict[str, str], optional
        :param cwd: Working directory for the server process.
        :type cwd: str, optional

        **SSE/Streamable Transport Parameters:**

        :param url: Server endpoint URL for HTTP-based transports.
        :type url: str
        :param headers: HTTP headers to include in requests.
        :type headers: dict[str, str], optional
        :param timeout: Connection timeout in seconds (streamable only).
        :type timeout: int, optional
        :param auth_config: Optional OAuth configuration for authenticated servers
        :type auth_config: dict, optional
        :param connection_params: Transport-specific connection parameters.
        :type connection_params: dict

        **OAuth Configuration (auth_config)**:

        :param client_id: OAuth client ID (optional for dynamic registration)
        :type client_id: str, optional
        :param client_secret: OAuth client secret
        :type client_secret: str, optional
        :param redirect_uri: OAuth redirect URI
        :type redirect_uri: str, optional
        :param discover_auth: Auto-discover auth requirements (default: True)
        :type discover_auth: bool, optional

        Example:
            Authenticated streamable client:

            .. code-block:: python

                client = MCPClient(
                    name="auth_client",
                    transport="streamable",
                    url="https://api.example.com/mcp",
                    auth_config={
                        "client_id": "my-client-id",
                        "client_secret": "my-secret",
                        "discover_auth": True
                    }
                )
        """
        self.name = name
        self.transport = transport
        self.connection_params = connection_params
        self.logger = logger
        self._session: Optional[ClientSession] = None
        self._context = None
        self._session_context = None

        # Authentication support
        self.auth_config = auth_config
        self._oauth_client: Optional[OAuthClient] = None
        self._access_token: Optional[str] = None
        self._auth_discovered = False

    async def connect(self):
        """
        Establish connection to the MCP server.

        This method initializes the transport-specific connection and sets up
        the MCP session. It's automatically called by other methods but can
        be called explicitly for early connection establishment.

        :raises ValueError: If an unsupported transport type is specified.
        :raises Exception: If connection establishment fails.
        """
        if self._session:
            return  # Already connected

        try:
            self.logger.debug(f"Connecting to server '{self.name}' via {self.transport}")

            if self.transport == "stdio":
                await self._connect_stdio()
            elif self.transport == "sse":
                await self._connect_sse()
            elif self.transport == "streamable":
                await self._connect_streamable()
            else:
                raise ValueError(f"Unknown transport: {self.transport}")

            self.logger.info(f"Connected to server '{self.name}'")

        except Exception as e:
            self.logger.error(f"Failed to connect to '{self.name}': {e}")
            raise

    async def disconnect(self):
        """
        Close the connection to the MCP server.

        Properly shuts down the MCP session and transport connection,
        cleaning up all associated resources.
        """
        if not self._session:
            return

        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._context:
                await self._context.__aexit__(None, None, None)

            self._session = None
            self._context = None
            self._session_context = None

            self.logger.debug(f"Disconnected from server '{self.name}'")

        except Exception as e:
            self.logger.warning(f"Error during disconnect from '{self.name}': {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available tools from the connected MCP server.

        :return: List of tool definitions, each containing name, description, and input schema.
        :rtype: list[dict[str, Any]]

        Example:
            .. code-block:: python

                tools = await client.list_tools()
                for tool in tools:
                    print(f"Tool: {tool['name']} - {tool['description']}")
        """
        await self.connect()

        result = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "inputSchema": getattr(tool, "inputSchema", {})
            }
            for tool in result.tools
        ]

    async def invoke_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a specific tool on the connected MCP server.

        :param name: Name of the tool to invoke.
        :type name: str
        :param arguments: Arguments to pass to the tool.
        :type arguments: dict[str, Any], optional
        :return: The tool's execution result.
        :rtype: Any

        Example:
            .. code-block:: python

                result = await client.invoke_tool(
                    "read_file",
                    {"path": "/config/settings.json"}
                )
        """
        await self.connect()

        result = await self._session.call_tool(name, arguments or {})
        return result.content

    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available resources from the connected MCP server.

        :return: List of resource definitions with URI, name, description, and MIME type.
        :rtype: list[dict[str, Any]]
        """
        await self.connect()

        result = await self._session.list_resources()
        return [
            {
                "uri": str(resource.uri),
                "name": getattr(resource, "name", ""),
                "description": getattr(resource, "description", ""),
                "mimeType": getattr(resource, "mimeType", "text/plain")
            }
            for resource in result.resources
        ]

    async def read_resource(self, uri: str) -> Any:
        """
        Read the contents of a specific resource from the server.

        :param uri: The URI of the resource to read.
        :type uri: str
        :return: The resource content.
        :rtype: Any
        """
        await self.connect()

        result = await self._session.read_resource(uri)
        return result.content

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available prompts from the connected MCP server.

        :return: List of prompt definitions with name, description, and arguments.
        :rtype: list[dict[str, Any]]
        """
        await self.connect()

        result = await self._session.list_prompts()
        return [
            {
                "name": prompt.name,
                "description": getattr(prompt, "description", ""),
                "arguments": getattr(prompt, "arguments", [])
            }
            for prompt in result.prompts
        ]

    async def _connect_stdio(self):
        """
        Establish connection using stdio transport.

        Launches the MCP server as a subprocess and establishes communication
        through standard input/output streams.
        """
        params = StdioServerParameters(
            command=self.connection_params["command"],
            args=self.connection_params.get("args", []),
            env=self.connection_params.get("env"),
            cwd=self.connection_params.get("cwd")
        )

        self._context = stdio_client(params)
        reader, writer = await self._context.__aenter__()

        self._session_context = ClientSession(reader, writer)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

    async def _connect_sse(self):
        """
        Establish connection using Server-Sent Events (SSE) transport.

        Connects to an HTTP endpoint that provides MCP communication
        through server-sent events.
        """
        # TODO: Client MCP authentication needs revisited, fails to connect after authentication
        await self._ensure_authenticated()

        headers = self.connection_params.get("headers", {})
        auth_headers = await self._get_auth_headers()
        headers.update(auth_headers)

        self._context = sse_client(
            url=self.connection_params["url"],
            headers=headers
        )
        reader, writer = await self._context.__aenter__()

        self._session_context = ClientSession(reader, writer)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

    async def _connect_streamable(self):
        """
        Establish connection using streamable HTTP transport.

        Connects to an HTTP endpoint that provides full bidirectional
        MCP communication through HTTP streaming.
        """
        # TODO: Client MCP authentication needs revisited, fails to connect after authentication
        # Skip OAuth flow if we already have auth headers (e.g., JWT bearer token)
        headers = self.connection_params.get("headers", {})
        if not headers.get("Authorization"):
            await self._ensure_authenticated()
            auth_headers = await self._get_auth_headers()
            headers.update(auth_headers)

        timeout = datetime.timedelta(
            seconds=self.connection_params.get("timeout", 30)
        )


        # Ensure proper Accept header for streamable transport
        if "Accept" not in headers:
            headers["Accept"] = "application/json, text/event-stream"

        # Check if we have a bearer token in headers
        auth = None
        if headers.get("Authorization", "").startswith("Bearer "):
            # Create a custom auth class for bearer tokens
            from httpx import Auth

            class BearerAuth(Auth):
                def __init__(self, token):
                    self.token = token

                def auth_flow(self, request):
                    request.headers["Authorization"] = f"Bearer {self.token}"
                    yield request

            token = headers["Authorization"].replace("Bearer ", "")
            auth = BearerAuth(token)
            # Remove from headers since we're using auth param
            headers.pop("Authorization", None)

        self._context = streamablehttp_client(
            url=self.connection_params["url"],
            headers=headers,
            timeout=timeout,
            auth=auth
        )

        try:
            reader, writer, _ = await self._context.__aenter__()
            self.logger.debug("Streamable HTTP connection established")
        except Exception as e:
            self.logger.error(f"Failed to establish streamable connection: {e}")
            raise

        self._session_context = ClientSession(reader, writer)
        self._session = await self._session_context.__aenter__()

        try:
            # TODO: Authentication with streamable transport times out during session initialization.
            # Server-side auth works correctly (returns 401 for unauthorized, 200 OK with SSE for authorized),
            # but the client session fails to initialize when connecting to authenticated servers.
            # Need to investigate why the SSE response handling fails with authentication enabled.
            await self._session.initialize()
            self.logger.debug("MCP session initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP session: {e}")
            raise

    async def _ensure_authenticated(self):
        """Ensure we have a valid access token for HTTP transports."""
        if self.transport not in ["sse", "streamable"] or not self.auth_config:
            return

        if not self._oauth_client:
            self._oauth_client = OAuthClient(
                client_id=self.auth_config.get("client_id"),
                client_secret=self.auth_config.get("client_secret"),
                redirect_uri=self.auth_config.get("redirect_uri", "http://localhost:8080/callback")
            )

        # Auto-discover authentication if enabled
        if self.auth_config.get("discover_auth", True) and not self._auth_discovered:
            try:
                server_url = self.connection_params.get("url")
                if server_url:
                    auth_info = await self._oauth_client.discover_authorization(server_url)
                    self._auth_discovered = True

                    if auth_info.get("protected"):
                        self.logger.info(f"Server '{self.name}' requires authentication")
                        # Get access token
                        scopes = self.auth_config.get("scopes", ["mcp:read"])
                        self._access_token = await self._oauth_client.get_access_token(
                            server_url,
                            scopes
                        )
            except Exception as e:
                self.logger.warning(f"Auth discovery failed: {e}")
                # Continue without auth - server might not require it

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers if authenticated."""
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    async def __aenter__(self):
        """
        Async context manager entry point.

        Automatically establishes connection when entering the context.

        :return: The connected client instance.
        :rtype: MCPClient
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.

        Automatically disconnects when exiting the context.

        :param exc_type: Exception type if an exception occurred.
        :param exc_val: Exception value if an exception occurred.
        :param exc_tb: Exception traceback if an exception occurred.
        """
        await self.disconnect()

    def __repr__(self):
        """
        Return string representation of the client.

        :return: String representation showing client name, transport, and connection status.
        :rtype: str
        """
        return f"MCPClient(name='{self.name}', transport='{self.transport}', connected={self._session is not None})"
