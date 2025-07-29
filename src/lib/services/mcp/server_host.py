#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Server Host module for managing platform-hosted Model Context Protocol servers.

This module provides functionality to host internal MCP servers using FastMCP
from the official SDK. It manages server lifecycle for platform tools that
need to be exposed via MCP.

Example:
    Basic usage:

    .. code-block:: python

        from src.lib.services.mcp_server_host import MCPServerHost
        from src.lib.services.mcp_directory import MCPDirectory

        # Create host with directory
        directory = MCPDirectory()
        host = MCPServerHost(directory)

        # Host a platform tool
        async def my_tool(x: int, y: int) -> int:
            return x + y

        await host.host_platform_tool(
            name="calculator",
            func=my_tool,
            port=8000
        )
"""

import asyncio
from typing import Dict, Callable, Optional, Any, List
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn

from src.lib.services.core.log import Logger
from src.lib.services.mcp.mcp_directory import MCPDirectory, ServerConfig

logger = Logger().get_logger()


class ServerHost:
    """
    Manages platform-hosted MCP servers using FastMCP.

    This class is responsible for hosting internal platform tools as MCP servers.
    It uses FastMCP from the official SDK and follows patterns from the lablib
    examples for server setup and lifecycle management.

    Attributes:
        directory (MCPDirectory): Directory for registering hosted servers.
        servers (dict): Dictionary of hosted FastMCP server instances.
        server_tasks (dict): Dictionary of asyncio tasks running the servers.
    """

    def __init__(self, directory: MCPDirectory):
        """
        Initialize the server host with a directory.

        :param directory: Directory for registering server configurations.
        :type directory: MCPDirectory
        """
        self.directory = directory
        self.servers: Dict[str, FastMCP] = {}
        self.server_tasks: Dict[str, asyncio.Task] = {}
        self.uvicorn_servers: Dict[str, uvicorn.Server] = {}
        logger.info("MCP Server Host initialized")

    async def host_platform_tool(
        self,
        name: str,
        func: Callable,
        port: int = 8000,
        host: str = "localhost",
        description: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None
    ) -> FastMCP:
        """
        Host a platform tool as an MCP server using FastMCP.

        This method creates a FastMCP server, registers the provided function
        as a tool, and starts the server using uvicorn. The server is
        automatically registered in the directory for client discovery.

        :param name: Unique name for the server.
        :type name: str
        :param func: Function to expose as an MCP tool.
        :type func: Callable
        :param port: Port to bind the server to.
        :type port: int
        :param host: Host address to bind the server to.
        :type host: str
        :param description: Optional description for the server.
        :type description: str, optional
        :param auth_config: Optional authentication configuration.
        :type auth_config: dict, optional
        :return: The created FastMCP server instance.
        :rtype: FastMCP

        Example:
            .. code-block:: python

                async def add_numbers(a: float, b: float) -> float:
                    '''Add two numbers together'''
                    return a + b

                server = await host.host_platform_tool(
                    name="math_server",
                    func=add_numbers,
                    port=8001,
                    description="Simple math operations"
                )
        """
        if name in self.servers:
            raise ValueError(f"Server '{name}' is already hosted")

        try:
            # Create FastMCP server following lablib pattern
            mcp = FastMCP(name=name, stateless_http=True)

            # Register the tool with its docstring as description
            tool_description = func.__doc__ or description or f"{func.__name__} tool"
            mcp.tool(description=tool_description)(func)

            # Create FastAPI app with MCP's session manager
            app = FastAPI(
                title=f"MCP Server: {name}",
                lifespan=lambda app: mcp.session_manager.run()
            )

            # Mount MCP app - the SDK will append /mcp to the mount path
            app.mount("/", mcp.streamable_http_app())

            # Add health check endpoint
            @app.get("/health")
            async def health_check():
                return {"status": "healthy", "server": name}

            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=False  # Reduce noise in logs
            )
            server = uvicorn.Server(config)

            # Start server in background task
            self.server_tasks[name] = asyncio.create_task(server.serve())
            self.servers[name] = mcp
            self.uvicorn_servers[name] = server

            # Register in directory for client discovery
            server_config = ServerConfig(
                name=name,
                accessibility="internal",
                hosting="local",
                transport="streamable",
                url=f"http://{host}:{port}/mcp",
                auth=auth_config,
                description=description or f"Platform tool: {name}",
                capabilities=["tools"]  # This server provides tools
            )
            self.directory.register(server_config)

            logger.info(f"Started MCP server '{name}' on {host}:{port}")
            return mcp

        except Exception as e:
            logger.error(f"Failed to start server '{name}': {e}")
            # Clean up on failure
            if name in self.server_tasks:
                self.server_tasks[name].cancel()
                del self.server_tasks[name]
            if name in self.servers:
                del self.servers[name]
            if name in self.uvicorn_servers:
                del self.uvicorn_servers[name]
            raise

    async def stop_server(self, name: str) -> bool:
        """
        Stop a hosted MCP server.

        :param name: Name of the server to stop.
        :type name: str
        :return: True if server was stopped, False if not found.
        :rtype: bool
        """
        if name not in self.servers:
            logger.warning(f"Server '{name}' not found")
            return False

        try:
            # Stop uvicorn server
            if name in self.uvicorn_servers:
                self.uvicorn_servers[name].should_exit = True

            # Cancel server task
            if name in self.server_tasks:
                self.server_tasks[name].cancel()
                try:
                    await self.server_tasks[name]
                except asyncio.CancelledError:
                    pass

            # Clean up references
            del self.servers[name]
            del self.server_tasks[name]
            if name in self.uvicorn_servers:
                del self.uvicorn_servers[name]

            # Remove from directory
            self.directory.remove(name)

            logger.info(f"Stopped server '{name}'")
            return True

        except Exception as e:
            logger.error(f"Error stopping server '{name}': {e}")
            return False

    async def stop_all(self) -> None:
        """
        Stop all hosted servers.

        This method gracefully shuts down all running MCP servers
        and should be called during application shutdown.
        """
        logger.info(f"Stopping {len(self.servers)} hosted servers")

        # Get list of server names (to avoid dict modification during iteration)
        server_names = list(self.servers.keys())

        # Stop each server
        for name in server_names:
            await self.stop_server(name)

        logger.info("All hosted servers stopped")

    def list_hosted_servers(self) -> List[Dict[str, Any]]:
        """
        List all currently hosted servers.

        :return: List of hosted server information.
        :rtype: list[dict]
        """
        result = []
        for name, mcp in self.servers.items():
            config = self.directory.get(name)
            result.append({
                "name": name,
                "url": config.url if config else None,
                "running": name in self.server_tasks and not self.server_tasks[name].done(),
                "tools_count": len(getattr(mcp, '_tools', {}))
            })
        return result

    def get_server(self, name: str) -> Optional[FastMCP]:
        """
        Get a hosted server instance by name.

        :param name: Name of the server.
        :type name: str
        :return: FastMCP server instance if found.
        :rtype: FastMCP or None
        """
        return self.servers.get(name)

    def __repr__(self) -> str:
        """Return string representation of the server host."""
        running = sum(1 for task in self.server_tasks.values() if not task.done())
        return f"MCPServerHost({running}/{len(self.servers)} servers running)"