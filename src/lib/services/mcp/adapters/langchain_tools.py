#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LangChain MCP Tool Adapter

This module provides adapters for integrating MCP tools with LangChain's tool system.
It converts MCP tools to LangChain StructuredTools and integrates with the existing
platform tool repository system.

Architecture Integration:
- Integrates with existing LangChainStructuredToolRepository
- Converts MCP tools to LangChain StructuredTool format
- Provides async tool execution with proper error handling
- Maintains tool metadata for discovery and management
"""

import asyncio
from typing import Any, Dict, List, Optional, Type
from functools import wraps
from pydantic import BaseModel, Field

from langchain_core.tools import StructuredTool
from langchain_core.callbacks import CallbackManagerForToolRun

from src.lib.core.log import Logger
from src.lib.services.agents.tool_repositories.langchain.structured_tool import LangChainStructuredToolRepository
from ..client import MCPClientManager
from ..registry import MCPRegistry

logger = Logger().get_logger()


class MCPToLangChainAdapter:
    """
    Adapter for converting MCP tools to LangChain StructuredTools.

    This class provides functionality to discover MCP tools from registered
    servers and convert them to LangChain-compatible tools that can be used
    with the existing agent reasoning engines.
    """

    class Config(BaseModel):
        """Configuration for MCP to LangChain adapter."""
        registry_config: Optional[Dict[str, Any]] = Field(
            default=None,
            description="MCP registry configuration"
        )
        tool_timeout: int = Field(
            default=30,
            description="Timeout for MCP tool execution in seconds"
        )
        auto_discover: bool = Field(
            default=True,
            description="Automatically discover tools from all enabled servers"
        )
        server_filter: Optional[List[str]] = Field(
            default=None,
            description="List of server names to include (if None, includes all)"
        )
        tag_filter: Optional[List[str]] = Field(
            default=None,
            description="List of tags to filter servers by"
        )

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the MCP to LangChain adapter.

        Args:
            config: Adapter configuration
        """
        if config is None:
            config = {}

        self.config = self.Config(**config)
        self.logger = logger

        # Initialize MCP registry
        registry_config = self.config.registry_config or {}
        self.registry = MCPRegistry(registry_config)

        # Get tool repository instance
        self.tool_repository = LangChainStructuredToolRepository()

    async def discover_and_register_tools(self) -> Dict[str, Any]:
        """
        Discover MCP tools and register them with the LangChain tool repository.

        Returns:
            Dictionary with discovery results and statistics
        """
        try:
            self.logger.info("Starting MCP tool discovery for LangChain integration")

            # Get servers to process
            servers = self._get_filtered_servers()
            if not servers:
                self.logger.warning("No servers found matching filters")
                return {"status": "warning", "message": "No servers found", "tools_registered": 0}

            # Discover capabilities for all servers
            all_capabilities = await self.registry.discover_all_capabilities(force_refresh=True)

            # Convert and register tools
            tools_registered = 0
            tools_failed = 0

            for server_name, capabilities in all_capabilities.items():
                if server_name not in [s.name for s in servers]:
                    continue

                server_config = self.registry.get_server(server_name)
                tools = capabilities.get('tools', [])

                self.logger.info(f"Converting {len(tools)} tools from server '{server_name}'")

                for tool_spec in tools:
                    try:
                        # Convert MCP tool to LangChain tool
                        langchain_tool = await self._convert_mcp_tool_to_langchain(
                            tool_spec, server_name, server_config
                        )

                        # Add to tool repository with metadata
                        metadata = {
                            "source": "mcp",
                            "server_name": server_name,
                            "server_transport": server_config.transport,
                            "server_tags": server_config.tags or [],
                            "mcp_tool_spec": tool_spec
                        }

                        result = self.tool_repository.add_tool(langchain_tool, metadata)

                        if result.status == "success":
                            tools_registered += 1
                            self.logger.debug(f"Registered MCP tool: {tool_spec['name']} from {server_name}")
                        else:
                            tools_failed += 1
                            self.logger.warning(f"Failed to register tool {tool_spec['name']}: {result.error_message}")

                    except Exception as e:
                        tools_failed += 1
                        self.logger.error(f"Error converting tool {tool_spec.get('name', 'unknown')}: {str(e)}")

            self.logger.info(f"MCP tool discovery complete: {tools_registered} registered, {tools_failed} failed")

            return {
                "status": "success",
                "servers_processed": len(all_capabilities),
                "tools_registered": tools_registered,
                "tools_failed": tools_failed,
                "capabilities": all_capabilities
            }

        except Exception as e:
            self.logger.error(f"MCP tool discovery failed: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "tools_registered": 0
            }

    async def _convert_mcp_tool_to_langchain(self, tool_spec: Dict[str, Any],
                                           server_name: str, server_config) -> StructuredTool:
        """
        Convert an MCP tool specification to a LangChain StructuredTool.

        Args:
            tool_spec: MCP tool specification
            server_name: Name of the MCP server
            server_config: Server configuration

        Returns:
            LangChain StructuredTool instance
        """
        tool_name = tool_spec['name']
        tool_description = tool_spec.get('description', f'MCP tool from {server_name}')
        input_schema = tool_spec.get('inputSchema', {})

        # Create Pydantic model for tool arguments
        args_model = self._create_args_model(tool_name, input_schema)

        # Create the tool execution function
        async def execute_tool(**kwargs) -> str:
            """Execute the MCP tool with given arguments."""
            try:
                # Get client manager for the server
                client_manager = self.registry.get_client_manager(server_name)
                if not client_manager:
                    raise ValueError(f"No client manager found for server '{server_name}'")

                # Execute the tool via MCP
                async with client_manager.connect() as session:
                    await session.initialize()

                    # Call the tool
                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, kwargs),
                        timeout=self.config.tool_timeout
                    )

                    # Extract result content
                    if hasattr(result, 'content') and result.content:
                        if isinstance(result.content, list) and len(result.content) > 0:
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                return content.text
                            elif isinstance(content, dict):
                                return content.get('text', str(content))
                            else:
                                return str(content)
                        else:
                            return str(result.content)
                    else:
                        return str(result)

            except asyncio.TimeoutError:
                error_msg = f"MCP tool '{tool_name}' timed out after {self.config.tool_timeout}s"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"MCP tool '{tool_name}' failed: {str(e)}"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"

        # Create sync wrapper for LangChain compatibility
        def sync_execute_tool(**kwargs) -> str:
            """Synchronous wrapper for the async tool execution."""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we need to handle this differently
                    # This is a common issue with LangChain tools in async environments
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, execute_tool(**kwargs))
                        return future.result(timeout=self.config.tool_timeout)
                else:
                    return loop.run_until_complete(execute_tool(**kwargs))
            except Exception as e:
                return f"Error executing MCP tool: {str(e)}"

        # Create the LangChain StructuredTool
        langchain_tool = StructuredTool(
            name=f"mcp_{server_name}_{tool_name}",
            description=tool_description,
            args_schema=args_model,
            func=sync_execute_tool,
            coroutine=execute_tool,  # Provide async version too
        )

        return langchain_tool

    def _create_args_model(self, tool_name: str, input_schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Create a Pydantic model for tool arguments based on JSON schema.

        Args:
            tool_name: Name of the tool
            input_schema: JSON schema for tool input

        Returns:
            Pydantic model class
        """
        # Extract properties from JSON schema
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])

        # Build field definitions for Pydantic model using proper annotations
        annotations = {}
        field_defaults = {}

        for prop_name, prop_spec in properties.items():
            prop_type = prop_spec.get('type', 'string')
            prop_description = prop_spec.get('description', '')
            prop_default = prop_spec.get('default')

            # Map JSON schema types to Python types
            python_type = self._map_json_type_to_python(prop_type)

            # Determine if field is required
            if prop_name in required:
                annotations[prop_name] = python_type
                field_defaults[prop_name] = Field(description=prop_description)
            else:
                annotations[prop_name] = Optional[python_type]
                field_defaults[prop_name] = Field(default=prop_default, description=prop_description)

        # If no properties, create a simple model
        if not properties:
            annotations['dummy'] = Optional[str]
            field_defaults['dummy'] = Field(default=None, description="No parameters required")

        # Create dynamic Pydantic model with proper annotations
        model_name = f"{tool_name.replace('-', '_').replace(' ', '_')}Args"

        # Create model class dynamically
        model_dict = {
            '__annotations__': annotations,
            **field_defaults
        }

        args_model = type(model_name, (BaseModel,), model_dict)

        return args_model

    def _map_json_type_to_python(self, json_type: str) -> Type:
        """Map JSON schema types to Python types."""
        type_mapping = {
            'string': str,
            'number': float,
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        return type_mapping.get(json_type, str)

    def _get_filtered_servers(self) -> List:
        """Get servers matching the configured filters."""
        # Get all servers
        servers = self.registry.list_servers(enabled_only=True)

        # Apply server name filter
        if self.config.server_filter:
            servers = [s for s in servers if s.name in self.config.server_filter]

        # Apply tag filter
        if self.config.tag_filter:
            servers = [s for s in servers if s.tags and any(tag in s.tags for tag in self.config.tag_filter)]

        return servers

    def get_registered_tools_info(self) -> Dict[str, Any]:
        """
        Get information about registered MCP tools.

        Returns:
            Dictionary with tool information and statistics
        """
        try:
            # Get all tools from repository
            tools_result = self.tool_repository.get_tools()

            if tools_result.status != "success":
                return {'error': f"Failed to get tools: {tools_result.error_message}"}

            # Filter MCP tools
            mcp_tools = []
            for tool_data in tools_result.tools:
                tool = tool_data.get('object')  # Note: repository uses 'object' key
                metadata = tool_data.get('metadata', {})

                if metadata.get('source') == 'mcp':
                    mcp_tools.append({
                        'name': tool.name,
                        'description': tool.description,
                        'server_name': metadata.get('server_name'),
                        'server_transport': metadata.get('server_transport'),
                        'server_tags': metadata.get('server_tags', [])
                    })

            # Group by server
            by_server = {}
            for tool in mcp_tools:
                server = tool['server_name']
                if server not in by_server:
                    by_server[server] = []
                by_server[server].append(tool)

            return {
                'total_mcp_tools': len(mcp_tools),
                'servers_with_tools': len(by_server),
                'tools_by_server': by_server,
                'all_mcp_tools': mcp_tools
            }

        except Exception as e:
            self.logger.error(f"Failed to get tool info: {str(e)}")
            return {'error': str(e)}

    def remove_mcp_tools(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove MCP tools from the tool repository.

        Args:
            server_name: If provided, only remove tools from this server

        Returns:
            Dictionary with removal results
        """
        try:
            # This would require extending the tool repository to support tool removal
            # For now, return a placeholder implementation
            self.logger.warning("Tool removal not yet implemented in base tool repository")
            return {
                'status': 'warning',
                'message': 'Tool removal not yet implemented'
            }

        except Exception as e:
            self.logger.error(f"Failed to remove MCP tools: {str(e)}")
            return {'status': 'error', 'error_message': str(e)}

    def __repr__(self) -> str:
        """String representation of the adapter."""
        return f"MCPToLangChainAdapter(servers={len(self.registry.list_servers())})"