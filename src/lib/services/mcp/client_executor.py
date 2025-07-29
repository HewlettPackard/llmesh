#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Client Executor

This module provides an MCP client executor for performing actions on
configured MCP servers. It executes requests using ephemeral connections,
allowing for flexible and stateless interactions with registered servers.
"""

from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from src.lib.services.mcp.mcp_directory import MCPDirectory, ServerConfig
from src.lib.services.core.log import Logger

logger = Logger().get_logger()


class ClientExecutor:
    """
    MCP Client Executor for performing actions on configured MCP servers.

    This class provides methods to interact with MCP servers using
    ephemeral connections. Each method call creates a new connection,
    performs the operation, and closes the connection.
    """

    def __init__(self, directory: MCPDirectory):
        """
        Initialize the ClientExecutor.

        :param directory: MCP directory containing server configurations.
        :type directory: MCPDirectory
        """
        self.directory = directory
        self.logger = logger

    async def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Invoke a tool on an MCP server."""
        return await self._execute_request(server_name, "invoke_tool", tool_name, arguments or {})

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools from an MCP server."""
        return await self._execute_request(server_name, "list_tools")

    async def list_resources(self, server_name: str) -> List[Dict[str, Any]]:
        """List available resources from an MCP server."""
        return await self._execute_request(server_name, "list_resources")

    async def read_resource(self, server_name: str, uri: str) -> Any:
        """Read a resource from an MCP server."""
        return await self._execute_request(server_name, "read_resource", uri)

    async def list_prompts(self, server_name: str) -> List[Dict[str, Any]]:
        """List available prompts from an MCP server."""
        return await self._execute_request(server_name, "list_prompts")

    async def get_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get a prompt from an MCP server."""
        return await self._execute_request(server_name, "get_prompt", prompt_name, arguments or {})

    async def _execute_request(self, server_name: str, method: str, *args) -> Any:
        """
        Execute a request on an MCP server using ephemeral connection.

        DRY principle: All transports follow the same pattern, so we handle them
        in one method.
        """
        config = self._get_server_config(server_name)

        try:
            # Create the appropriate client based on transport
            if config.transport == "stdio":
                params = StdioServerParameters(
                    command=config.command,
                    args=config.args or [],
                    env=config.env
                )
                client_context = stdio_client(params)

            elif config.transport == "sse":
                headers = self._get_auth_headers(config)
                client_context = sse_client(config.url, headers=headers)

            elif config.transport == "streamable":
                headers = self._get_auth_headers(config)
                client_context = streamablehttp_client(config.url, headers=headers)

            else:
                raise ValueError(f"Unsupported transport: {config.transport}")

            # Execute the request with ephemeral connection
            async with client_context as client_args:
                # Handle different return signatures
                if config.transport == "streamable":
                    reader, writer, _ = client_args
                else:
                    reader, writer = client_args

                async with ClientSession(reader, writer) as session:
                    await session.initialize()

                    # Execute the appropriate method
                    if method == "invoke_tool":
                        result = await session.call_tool(args[0], args[1])
                        # Extract text content from the result
                        if result.content and len(result.content) > 0:
                            # Return the text from the first content item
                            return result.content[0].text
                        return None

                    elif method == "list_tools":
                        result = await session.list_tools()
                        return [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema
                            }
                            for tool in result.tools
                        ]

                    elif method == "list_resources":
                        result = await session.list_resources()
                        return [
                            {
                                "uri": resource.uri,
                                "name": resource.name,
                                "description": resource.description,
                                "mimeType": resource.mimeType
                            }
                            for resource in result.resources
                        ]

                    elif method == "read_resource":
                        result = await session.read_resource(args[0])
                        return result.contents

                    elif method == "list_prompts":
                        result = await session.list_prompts()
                        return [
                            {
                                "name": prompt.name,
                                "description": prompt.description,
                                "arguments": prompt.arguments
                            }
                            for prompt in result.prompts
                        ]

                    elif method == "get_prompt":
                        result = await session.get_prompt(args[0], args[1])
                        return result

                    else:
                        raise ValueError(f"Unknown method: {method}")

        except Exception as e:
            self.logger.error(f"Request failed for '{server_name}' ({method}): {e}", exc_info=True)
            raise

    def _get_server_config(self, server_name: str) -> ServerConfig:
        """Get server configuration from directory."""
        config = self.directory.get(server_name)
        if not config:
            raise ValueError(f"Server '{server_name}' not found in directory")
        return config

    def _get_auth_headers(self, config: ServerConfig) -> Dict[str, str]:
        """Get authentication headers if configured."""
        headers = {}
        if config.auth and config.auth.get("bearer_token"):
            headers["Authorization"] = f"Bearer {config.auth['bearer_token']}"
        return headers

    async def test_connection(self, server_name: str) -> bool:
        """Test if a server is reachable and responsive."""
        try:
            await self.list_tools(server_name)
            return True
        except Exception as e:
            self.logger.warning(f"Connection test failed for '{server_name}': {e}")
            return False

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ClientExecutor(servers={len(self.directory)})"