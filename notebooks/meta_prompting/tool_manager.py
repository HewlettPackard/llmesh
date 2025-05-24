#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dynamically Load LangChain Tools into TOOLS List
"""

import importlib
from typing import List, Dict, Any
from langchain.tools import StructuredTool


def load_tools(path: str, modules: List) -> List[Dict[str, Any]]:
    """
    Dynamically imports tool modules and extracts metadata into the TOOLS list.

    Returns:
        List[Any]: List of tool objects.
        List[Dict[str, Any]]: List of tool metadata dictionaries.
    """
    tools_objects = []
    tools_metadata = []
    for module_name in modules:
        try:
            module_path = path + "." + module_name
            module = importlib.import_module(module_path)
            # Detect StructuredTool instances within the module
            tool_objects = [
                getattr(module, var_name) for var_name in dir(module)
                if isinstance(getattr(module, var_name, None), StructuredTool)
            ]
            # Extract metadata for each detected tool
            for tool in tool_objects:
                tools_metadata.append(_extract_tool_metadata(tool))
            tools_objects.append(tool_objects[0])
        except Exception as e:  # pylint: disable=W0718
            print(f"Error loading tool from {module_path}: {e}")
    return tools_objects, tools_metadata

def _extract_tool_metadata(tool: StructuredTool) -> Dict[str, Any]:
    parameters = {}
    # Extract arguments from tool.args instead of args_schema
    if tool.args:
        for arg_name, arg_info in tool.args.items():
            param_data = {
                "description": arg_info["description"]
            }
            # Determine type from the `default` value if available, else use type hint
            if "default" in arg_info:
                param_data["type"] = _get_type_from_value(arg_info["default"])
                param_data["required"] = False  # Default values mean the field is optional
            else:
                param_data["type"] = arg_info["type"]
                param_data["required"] = True  # No default means required
            parameters[arg_name] = param_data
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": parameters,
    }

def _get_type_from_value(value: Any) -> str:
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null"
    }
    return type_mapping.get(type(value), "unknown")


if __name__ == "__main__":
    import json
    # List of tool modules to import
    TOOL_PATH = "notebooks.meta_prompting.tools"
    TOOL_MODULES = [
        "get_order_status",
        "modify_order",
        "cancel_order",
        "track_shipment",
        "initiate_return",
        "check_refund",
        "process_refund",
        "order_history",
        "handle_complaint",
        "escalate_to_human",
        "update_account",
        "get_faq",
        "case_resolution"
    ]

    # Generate TOOLS dynamically
    TOOLS_OBJECTS, TOOLS = load_tools(TOOL_PATH, TOOL_MODULES)
    print(json.dumps(TOOLS, indent=2))
