#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compatibility shim for MCPServer.

This module maintains backward compatibility by redirecting to FastMCP
from the official SDK.
"""

from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from src.lib.services.core.log import Logger
logger = Logger().get_logger()


class MCPServer:
    """
    Compatibility wrapper for MCPServer.

    The old MCPServer wrapped FastMCP. This shim provides the same
    interface but delegates directly to FastMCP.
    """

    def __init__(
        self,
        name: str,
        transport: str = "stdio",
        token_verifier: Optional[Any] = None,
        auth_settings: Optional[Dict[str, Any]] = None
    ):
        """Initialize compatibility server."""
        self.name = name
        self.transport = transport
        self.logger = logger
        self.token_verifier = token_verifier

        # Create FastMCP instance
        if transport in ["sse", "streamable"] and token_verifier:
            # Import auth components
            from mcp.server.auth.settings import AuthSettings as MCPAuthSettings

            # Convert auth settings
            auth_settings_obj = None
            if auth_settings:
                auth_settings_obj = MCPAuthSettings(
                    issuer_url=auth_settings.get("issuer_url"),
                    resource_server_url=auth_settings.get("resource_server_url"),
                    required_scopes=auth_settings.get("required_scopes", [])
                )

            self.mcp = FastMCP(
                name=name,
                auth_server_provider=token_verifier,
                auth=auth_settings_obj
            )
            self.logger.info(f"Created authenticated {transport} server '{name}'")
        else:
            # Standard FastMCP without auth
            self.mcp = FastMCP(name=name)
            if transport == "stdio" and token_verifier:
                self.logger.warning("Authentication not supported for stdio transport, ignoring auth settings")


    def __repr__(self):
        """Return string representation of the server."""
        return f"MCPServer(name='{self.name}', transport='{self.transport}')"
