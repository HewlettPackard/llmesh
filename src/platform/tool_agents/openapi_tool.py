#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to manage an OpenAPI spec

Note: 5G APIs have been found in https://github.com/jdegre/5GC_APIs
and can be tested in https://jdegre.github.io/parser.html
"""

import os
from typing import Optional, Type, Any
import yaml
import jsonref
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from libs.chat.prompt_render import PromptRender
from libs.core.config import Config
from libs.core.log import Logger


config = Config('src/platform/tool_agents/config.yaml').get_settings()
logger = Logger().configure(config['logger']).get_logger()

SPECIFICATIONS_CONFIG = config["function"]["specifications"]
PROMPT_CONFIG = config["prompts"]
prompt = PromptRender.create(PROMPT_CONFIG)
OPENAPI_TOOL_NAME = "OpenAPI ManagerTool"
OPENAPI_TOOL_DESCRIPTION = prompt.load("tool_open_api").content
OPENAPI_FIELD_ACTION_DESCRIPTION = prompt.load("field_open_api_action").content
OPENAPI_FIELD_VALUE_DESCRIPTION = prompt.load("field_open_api_value").content


class OpenApiManager():  # pylint: disable=R0903
    "Class to support OpenAPI management"

    def __init__(self, spec_config):
        self.path = spec_config["path"]
        self.schema = {}
        self.resolved_schema = {}

    def call(self, action, value=None):
        "Call the selected OpenAPI helper function"
        action_map = {
            "ListOpenApis": (self._list_open_apis, ""),
            "SelectOpenApi": (self._select_open_api, "open_api"),
            "GetOpenApiVersion": (self._get_open_api_version, ""),
            "GetInfo": (self._get_info, ""),
            "GetServers": (self._get_servers, ""),
            "GetTags": (self._get_tags, ""),
            "GetMethodsByTag": (self._get_methods_by_tag, "tag"),
            "GetMethodById": (self._get_method_by_id, "operation_id"),
            "GetRequestBody": (self._get_request_body, "request_name"),
            "GetResponse": (self._get_response, "response_name")
        }
        if action in action_map:
            func, param = action_map[action]
            if param:
                if value is not None:
                    return func(value)
                raise ValueError(f"Action '{action}' requires a parameter '{param}'.")
            return func()
        raise ValueError(f"Action '{action}' is not recognized.")

    def _list_open_apis(self):
        files = [f.name for f in os.scandir(self.path) if not f.is_dir()]
        return files

    def _select_open_api(self, open_api):
        try:
            file_path = os.path.join(self.path, open_api)
            # Load the YAML schema from a file
            with open(file_path, 'r', encoding="utf-8") as file:
                self.schema = yaml.safe_load(file)
            # Resolve $ref references
            self._replace_references()
            status = "OpenAPI schema successfully loaded and resolved."
        except Exception as e:  # pylint: disable=W0718
            status = f"Failed to load or resolve OpenAPI schema: {e}"
        return status

    def _replace_references(self):
        self.resolved_schema = jsonref.replace_refs(self.schema, loader=self._reference_loader)

    def _reference_loader(self, uri):
        # Check if the file exists locally
        file_path = os.path.join(self.path, uri)
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        # Load the file based on its extension
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                return yaml.safe_load(f)
            raise ValueError(f"Unsupported file format for URI: {uri}")

    def _get_open_api_version(self):
        specifications = self.resolved_schema
        return specifications.get("openapi")

    def _get_info(self):
        specifications = self.resolved_schema
        return specifications.get("info")

    def _get_servers(self):
        specifications = self.resolved_schema
        return specifications.get("servers")

    def _get_tags(self):
        specifications = self.resolved_schema
        # Initialize an empty set to store unique tags
        tags = set()
        # Get the 'paths' section from the specifications
        paths = specifications.get("paths", {})
        # Iterate over each path and its operations
        for path, operations in paths.items():  # pylint: disable=W0612
            for operation, details in operations.items():
                # Skip if the operation is not an HTTP method (like 'parameters')
                if operation not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    continue
                # Get the tags for the operation
                operation_tags = details.get("tags", [])
                tags.update(operation_tags)
        return list(tags)  # Convert set to list to return

    def _get_methods_by_tag(self, tag):
        specifications = self.resolved_schema
        methods = []
        for path_name, path_schema in specifications.get("paths", {}).items():
            for method_name, method_schema in path_schema.items():
                if tag in method_schema.get("tags", []):
                    methods.append({
                        "id": method_schema.get("operationId"),
                        "path": path_name,
                        "method": method_name,
                        "summary": method_schema.get("summary"),
                    })
        return methods

    def _get_method_by_id(self, operation_id):
        specifications = self.schema
        for path_name, path_schema in specifications.get("paths", {}).items():
            for method_name, method_schema in path_schema.items():
                if operation_id == method_schema.get("operationId"):
                    return {
                        "id": method_schema.get("operationId"),
                        "path": path_name,
                        "method": method_name,
                        "summary": method_schema.get("summary"),
                        "description": method_schema.get("description"),
                        "request_body": method_schema.get("requestBody"),
                        "responses": method_schema.get("responses"),
                    }
        return None

    def _get_request_body(self, request_name):
        specifications = self.resolved_schema
        return specifications.get("components", {}).get("schemas", {}).get(request_name)

    def _get_response(self, response_name):
        specifications = self.resolved_schema
        return specifications.get("components", {}).get("responses", {}).get(response_name)


class OpenApiManagerToolInput(BaseModel):
    "Input schema for Dashboard API tool"

    action: str = Field(description=OPENAPI_FIELD_ACTION_DESCRIPTION)
    value: Optional[str] = Field(description=OPENAPI_FIELD_VALUE_DESCRIPTION)


class OpenApiManagerTool(BaseTool):
    "Class of the Dashboard tool"

    name: str = OPENAPI_TOOL_NAME
    description: str = OPENAPI_TOOL_DESCRIPTION
    args_schema: Type[BaseModel] = OpenApiManagerToolInput
    manager: Any = OpenApiManager(SPECIFICATIONS_CONFIG)

    def _run(self, action: str, value: Optional[str] = None) -> str:  # pylint: disable=W0221
        response = self.manager.call(action, value)
        return response

    def __call__(self, action: str, value: Optional[str] = None) -> str:
        return self._run(action, value)


if __name__ == "__main__":
    tool = OpenApiManagerTool()
    apis = tool("ListOpenApis")
    logger.debug(apis)
    apis = tool("SelectOpenApi", "TS29502_Nsmf_PDUSession.yaml")
    logger.debug(apis)
    apis = tool("GetInfo")
    logger.debug(apis)
    apis = tool("GetServers")
    logger.debug(apis)
    apis = tool("GetTags")
    logger.debug(apis)
    apis = tool("GetMethodsByTag", "Individual SM context")
    logger.debug(apis)
    apis = tool("GetMethodById", "UpdateSmContext")
    logger.debug(apis)
    # apis = tool("GetRequestBody", "SmContextRetrieveData")
    apis = tool("GetRequestBody", "SmContextUpdateData")
    logger.debug(apis)
    apis = tool("GetResponse", "VsmfUpdateResponse200")
    logger.debug(apis)
