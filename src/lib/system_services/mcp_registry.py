#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Registry module for centralized Model Context Protocol management within LATMesh.

This module provides the MCPRegistry class, which serves as the central hub for
managing MCP servers and clients in the platform. It handles registration, discovery, and
interaction with both locally-hosted and remote MCP servers based on configurable
accessibility and hosting properties.

Example:
    Basic registry usage:

    .. code-block:: python

        from src.lib.system_services.mcp_registry import MCPRegistry

        # Create registry
        registry = MCPRegistry()

        # Register a server
        await registry.register_server(
            name="filesystem",
            accessibility="internal",
            hosting="local",
            config={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]}
        )

        # Discover and invoke tools
        tools = await registry.discover_tools()
        result = await registry.invoke_tool("filesystem", "read_file", {"path": "/config.json"})
"""
import asyncio
from typing import Dict, List, Optional, Any, Literal

from src.lib.core.log import Logger
from src.lib.core.config import Config
from src.lib.system_services.mcp_client import MCPClient
from src.lib.system_services.mcp_server import MCPServer
from src.lib.system_services.mcp_auth import IntrospectionTokenVerifier, JWTTokenVerifier

logger = Logger().get_logger()


class ServerEntry:
    """
    Registry entry representing an MCP server configuration and state.

    This class encapsulates all information about a registered MCP server,
    including its configuration, accessibility rules, hosting type, and
    runtime state such as active client connections and server instances.

    Attributes:
        name (str): Unique server identifier.
        accessibility (str): Server accessibility level ("internal", "external", "both").
        hosting (str): Hosting type ("local", "remote").
        config (dict): Server-specific configuration parameters.
        auth_config (Optional[dict]): Optional authentication configuration for the server.
        client (MCPClient): Active client connection to the server, if any.
        server (MCPServer): Server instance for locally-hosted internal servers.
        process: Process handle for locally-hosted external servers.
    """

    def __init__(
        self,
        name: str,
        accessibility: Literal["internal", "external", "both"],
        hosting: Literal["local", "remote"],
        config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.accessibility = accessibility
        self.hosting = hosting
        self.config = config
        self.auth_config = auth_config
        self.client: Optional[MCPClient] = None
        self.server: Optional[MCPServer] = None
        self.process = None


class MCPRegistry:
    """
    Central registry for managing Model Context Protocol (MCP) servers.

    This class provides a unified interface for registering, discovering, and
    interacting with MCP servers. It manages servers based on two key properties:
    accessibility (who can access the server) and hosting (where the server runs).

    The registry supports:
    - Internal servers: Platform-specific tools accessible only to internal services
    - External servers: Third-party MCP servers accessible to external clients
    - Both: Servers accessible to both internal and external clients
    - Local hosting: Servers running on the same machine as the platform
    - Remote hosting: Servers running on external infrastructure

    Attributes:
        servers (dict): Dictionary mapping server names to ServerEntry instances.
        logger: Logger instance for debugging and error reporting.
        config (dict): Registry configuration loaded from optional config file.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the MCP registry with optional configuration file.

        :param config_file: Path to configuration file containing server definitions.
        :type config_file: str, optional

        Example:
            Create registry with configuration file:

            .. code-block:: python

                registry = MCPRegistry("/config/mcp_servers.yaml")
        """
        self.servers: Dict[str, ServerEntry] = {}
        self.logger = logger
        self.config = {}
        if config_file:
            self.config = Config(config_file=config_file).get_settings()
            if self.config and self.config.get('mcp_servers'):
                asyncio.run(self.register_servers_from_config())

    async def register_servers_from_config(self):
        """
        Register all servers defined in the configuration file.

        This method processes the configuration file and registers each server
        defined in the 'mcp_servers' section. It handles missing keys gracefully
        and logs any registration failures.
        """
        servers = self.config.get('mcp_servers', [])
        for server_config in servers:
            try:
                await self.register_server(
                    name=server_config['name'],
                    accessibility=server_config['accessibility'],
                    hosting=server_config['hosting'],
                    config=server_config.get('config', {}),
                    auth_config=server_config.get('auth', None)
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
        config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an MCP server with the registry.

        This method creates a new server entry with the specified properties and
        configuration. It supports both local and remote servers with different
        accessibility levels.

        :param name: Unique server identifier within the registry.
        :type name: str
        :param accessibility: Server accessibility level determining who can access it.
            - "internal": Only platform services can access
            - "external": Only external clients can access
            - "both": Both platform services and external clients can access
        :type accessibility: Literal["internal", "external", "both"]
        :param hosting: Server hosting type determining where it runs.
            - "local": Server runs on the same machine as the platform
            - "remote": Server runs on external infrastructure
        :type hosting: Literal["local", "remote"]
        :param config: Server-specific configuration parameters.
            For local servers: command, args, env, transport (optional)
            For remote servers: url, transport, headers (optional)
            For internal servers: use_internal_server, setup_callback (optional)
        :type config: dict[str, Any]
        :param auth_config: Optional authentication configuration
            For servers (Resource Servers):
                - token_verifier: Token verification strategy ("introspection" or "jwt")
                - introspection_endpoint: For introspection verification
                - jwks_uri: For JWT verification
                - issuer_url: Authorization server URL
                - required_scopes: List of required scopes
            For clients:
                - client_id: OAuth client ID
                - client_secret: OAuth client secret
                - scopes: Requested scopes
        :type auth_config: dict[str, Any], optional

        Example:
            Register an authenticated server:

            .. code-block:: python

                success = await registry.register_server(
                    name="protected_api",
                    accessibility="external",
                    hosting="local",
                    config={
                        "transport": "streamable",
                        "host": "localhost",
                        "port": 8080
                    },
                    auth_config={
                        "token_verifier": "introspection",
                        "introspection_endpoint": "https://auth.example.com/introspect",
                        "issuer_url": "https://auth.example.com",
                        "required_scopes": ["mcp:read", "mcp:write"]
                    }
                )
        """
        try:
            if name in self.servers:
                self.logger.warning(f"Server '{name}' already registered, updating")

            processed_config = self._process_webapp_config(config)
            entry = ServerEntry(name, accessibility, hosting, processed_config, auth_config)
            self.servers[name] = entry

            self.logger.info(f"Registered {hosting} {accessibility} server: {name}")
            if auth_config:
                self.logger.info(f"Server '{name}' configured with authentication")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register server '{name}': {e}")
            return False

    def _process_webapp_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webapp configuration for tools.

        Converts legacy webapp configuration (ip, port, ssh_cert) to MCP-compatible
        configuration including SSL certificate handling.

        :param config: Original configuration dictionary
        :return: Processed configuration with SSL parameters
        """
        processed = config.copy()

        # Handle 'ip' to 'host' conversion
        if "ip" in processed and "host" not in processed:
            processed["host"] = processed.pop("ip")

        # Handle SSL certificate configuration
        if "ssh_cert" in processed:
            ssh_cert = processed.pop("ssh_cert")
            if ssh_cert == "adhoc":
                # For adhoc certificates, uvicorn will generate them
                processed["ssl_certfile"] = None
                processed["ssl_keyfile"] = None
                processed["ssl_context"] = "adhoc"
            elif isinstance(ssh_cert, dict):
                # For provided certificates
                if "certfile" in ssh_cert:
                    processed["ssl_certfile"] = ssh_cert["certfile"]
                if "keyfile" in ssh_cert:
                    processed["ssl_keyfile"] = ssh_cert["keyfile"]

        return processed

    async def start_server(self, name: str) -> bool:
        """
        Start a locally-hosted MCP server.

        This method starts servers that are configured for local hosting. For
        internal servers (use_internal_server=True), it creates an MCPServer
        instance and calls the setup callback if provided. For external servers,
        it prepares them for stdio-based communication.

        :param name: Name of the registered server to start.
        :type name: str
        :return: True if server started successfully, False otherwise.
        :rtype: bool

        Example:
            .. code-block:: python

                success = await registry.start_server("platform_internal")
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

                # Create token verifier if auth is configured
                token_verifier = None
                auth_settings = None

                if entry.auth_config and transport in ["sse", "streamable"]:
                    # Create token verifier based on configuration
                    verifier_type = entry.auth_config.get("token_verifier")

                    if verifier_type == "introspection":
                        token_verifier = IntrospectionTokenVerifier(
                            introspection_endpoint=entry.auth_config["introspection_endpoint"],
                            server_url=f"http://{entry.config.get('host', 'localhost')}:{entry.config.get('port', 8000)}",
                            client_id=entry.auth_config.get("client_id"),
                            client_secret=entry.auth_config.get("client_secret")
                        )
                    elif verifier_type == "jwt":
                        token_verifier = JWTTokenVerifier(
                            jwks_uri=entry.auth_config.get("jwks_uri"),
                            issuer=entry.auth_config.get("issuer_url"),
                            audience=entry.auth_config.get("audience"),
                            algorithms=entry.auth_config.get("algorithms", ["RS256"])
                        )

                    # Create auth settings
                    if entry.auth_config.get("issuer_url"):
                        auth_settings = {
                            "issuer_url": entry.auth_config["issuer_url"],
                            "resource_server_url": f"http://{entry.config.get('host', 'localhost')}:{entry.config.get('port', 8000)}",
                            "required_scopes": entry.auth_config.get("required_scopes", [])
                        }

                entry.server = MCPServer(
                    name,
                    transport,
                    token_verifier=token_verifier,
                    auth_settings=auth_settings
                )

                # Allow registration of tools before starting
                if "setup_callback" in entry.config:
                    await entry.config["setup_callback"](entry.server)

                # Prepare start kwargs including SSL if configured
                start_kwargs = {
                    "host": entry.config.get("host", "localhost"),
                    "port": entry.config.get("port", 8000)
                }

                # Add SSL configuration if present
                for ssl_key in ["ssl_certfile", "ssl_keyfile", "ssl_context"]:
                    if ssl_key in entry.config:
                        start_kwargs[ssl_key] = entry.config[ssl_key]

                await entry.server.start(**start_kwargs)
            else:
                # For external MCP servers, just track that we expect stdio
                self.logger.info(f"Server '{name}' configured for local hosting")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start server '{name}': {e}")
            return False

    async def get_client(self, name: str) -> Optional[MCPClient]:
        """
        Get a client connection to a registered MCP server.

        This method creates and returns a connected MCPClient instance for the
        specified server. It handles different transport types and connection
        parameters based on the server's configuration.

        :param name: Name of the registered server to connect to.
        :type name: str
        :return: Connected MCPClient instance, or None if connection failed.
        :rtype: MCPClient or None

        Example:
            .. code-block:: python

                client = await registry.get_client("filesystem")
                if client:
                    tools = await client.list_tools()
        """
        if name not in self.servers:
            self.logger.error(f"Server '{name}' not found")
            return None

        entry = self.servers[name]

        # Reuse existing client if available
        if entry.client and entry.client._session:
            return entry.client

        try:
            # Prepare auth config for client if available
            client_auth_config = None
            if entry.auth_config:
                # Extract client-side auth settings
                client_auth_config = {
                    "client_id": entry.auth_config.get("client_id"),
                    "client_secret": entry.auth_config.get("client_secret"),
                    "scopes": entry.auth_config.get("scopes", ["mcp:read"]),
                    "discover_auth": entry.auth_config.get("discover_auth", True)
                }

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
                        cwd=entry.config.get("cwd"),
                        auth_config=client_auth_config
                    )
                else:
                    # Local HTTP-based server
                    client = MCPClient(
                        name=name,
                        transport=transport,
                        url=f"http://{entry.config.get('host', 'localhost')}:{entry.config.get('port', 8000)}/mcp",
                        auth_config=client_auth_config
                    )
            else:
                # Remote servers
                client = MCPClient(
                    name=name,
                    transport=entry.config["transport"],
                    url=entry.config["url"],
                    headers=entry.config.get("headers"),
                    auth_config=client_auth_config
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
        Discover available tools from registered MCP servers.

        This method connects to registered servers and retrieves their available
        tools, optionally filtering by accessibility level. It returns a mapping
        of server names to their tool lists.

        :param accessibility_filter: Filter servers by accessibility level.
            Valid values: "internal", "external", "both", or None for all servers.
        :type accessibility_filter: str, optional
        :return: Dictionary mapping server names to lists of their available tools.
        :rtype: dict[str, list[dict[str, Any]]]

        Example:
            .. code-block:: python

                # Discover all tools
                all_tools = await registry.discover_tools()

                # Discover only internal tools
                internal_tools = await registry.discover_tools("internal")
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
        Invoke a specific tool on a registered MCP server.

        This method connects to the specified server and executes the named tool
        with the provided arguments. It handles connection establishment and
        error reporting.

        :param server_name: Name of the registered server containing the tool.
        :type server_name: str
        :param tool_name: Name of the tool to invoke on the server.
        :type tool_name: str
        :param arguments: Arguments to pass to the tool, if any.
        :type arguments: dict[str, Any], optional
        :return: The result returned by the tool execution.
        :rtype: Any

        :raises ValueError: If the server cannot be found or connected to.

        Example:
            .. code-block:: python

                result = await registry.invoke_tool(
                    "filesystem",
                    "read_file",
                    {"path": "/config/settings.json"}
                )
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

        This method returns a list of registered servers, optionally filtered by
        accessibility level and hosting type. Each server entry includes basic
        information about its configuration and connection status.

        :param accessibility_filter: Filter by accessibility level ("internal", "external", "both").
        :type accessibility_filter: str, optional
        :param hosting_filter: Filter by hosting type ("local", "remote").
        :type hosting_filter: str, optional
        :return: List of dictionaries containing server information.
        :rtype: list[dict[str, Any]]

        Example:
            .. code-block:: python

                # List all servers
                all_servers = registry.list_servers()

                # List only local servers
                local_servers = registry.list_servers(hosting_filter="local")
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
        """
        Clean up all connections and resources managed by the registry.

        This method gracefully shuts down all active client connections and
        stops all locally-hosted servers. It should be called during application
        shutdown to ensure proper resource cleanup.

        Example:
            .. code-block:: python

                # During application shutdown
                await registry.cleanup()
        """
        for entry in self.servers.values():
            if entry.client:
                await entry.client.disconnect()
            if entry.server:
                await entry.server.stop()
