#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decorator-based utility for enhancing function calls within the Athon LLM Platform.

This module provides the AthonTool class, a decorator for augmenting functions
with logging, dynamic invocation capabilities, and web application integration.
It is intended to facilitate the development of modular and reusable components
within the Athon project, promoting efficient development practices and easy
integration. The module allows for enhanced function calls with automatic logging,
manifest generation, and supports execution within a Flask-based web framework.

Example:
    @AthonTool(config, logger)
    def add_function(a, b):
        return f"Sum: {a + b}"
"""

import os
import inspect
import copy
from typing import Any, List, Optional, Union
from flask import Flask, request, jsonify
from pydantic import BaseModel, Field, ValidationError
from src.lib.core.template_engine import TemplateEngine
from src.lib.core.config import Config
from src.lib.core.log import Logger


class AthonTool:
    """
    A decorator class designed to enhance functions by applying additional logic
    and utilizing provided config and a logger. It can manually invoke decorated
    functions, retrieve tool manifests, and run associated web applications.
    """

    class Manifest(BaseModel):
        """
        Configuration for the tool.
        """
        name: str = Field(
            ...,
            description="The name of the tool."
        )
        function: str = Field(
            ...,
            description="The function associated with the tool."
        )
        description: str = Field(
            ...,
            description="A description of the tool."
        )
        arguments: Optional[List['AthonTool.Argument']] = Field(
            None,
            description="A list of arguments for the tool."
        )
        interface: Optional['AthonTool.Interface'] = Field(
            None,
            description="The interface configuration for the tool."
        )
        return_direct: Optional[bool] = Field(
            False,
            description="Return the response of the tool without any re-work."
        )

    class Argument(BaseModel):
        """
        Configuration for an argument in the tool.
        """
        name: str = Field(
            ...,
            description="The name of the argument."
        )
        type: str = Field(
            ...,
            description="The type of the argument."
        )
        description: str = Field(
            ...,
            description="A description of the argument."
        )
        class Config:
            "Extra option"
            extra = "allow"  # Allows extra fields not explicitly defined in the model


    class Interface(BaseModel):
        """
        Configuration for the interface of the tool.
        """
        fields: List['AthonTool.InterfaceField'] = Field(
            ...,
            description="A list of fields for the interface."
        )

    class InterfaceField(BaseModel):
        """
        Configuration for a field in the interface.
        """
        name: str = Field(
            ...,
            description="The name of the field."
        )
        type: str = Field(
            ...,
            description="The type of the field."
        )
        class Config:
            "Extra option"
            extra = "allow"  # Allows extra fields not explicitly defined in the model


    def __init__(
        self,
        config: Union[dict, str, None] = None,
        logger: Optional[Any] = None):
        """
        Initialize the AthonTool instance with a configuration and logger.

        :param config: A dictionary containing the tool's configuration, 
            or a path to a config file, or None for default.
        :param logger: A logger instance for logging purposes, or None 
            to create/use a default logger.
        """
        self.config = self._init_config(config)
        self.logger = self._init_logger(logger)
        self.function = None
        self.app = None

    def _init_config(self, config) -> dict:
        """
        Initialize and validate the tool configuration.

        :param config: A dictionary containing the tool's configuration, 
            or a path to a config file, or None for default.
        :return: The validated configuration dictionary.
        """
        try:
            if config is None:
                config = self._auto_detect_config_from_caller()
            if isinstance(config, str):
                config = Config(config).get_settings()
            validated_manifest = self._validate_tool_manifest(config.get("tool", {}))
            config["tool"] = validated_manifest
        except Exception as e:  # pylint: disable=W0718
            raise ValueError(f"Invalid configuration: {e}") from e
        return config

    def _auto_detect_config_from_caller(self) -> dict:
        """
        Auto-detects a config by deriving a default path from the caller's file.
        If the file exists, load it. Otherwise return an empty dict or default.
        """
        stack = inspect.stack()
        main_py_frame = None
        for frame_info in stack:
            # For example, look for a file that ends with "main.py"
            if frame_info.filename.endswith('main.py'):
                main_py_frame = frame_info
                break
        if main_py_frame:
            caller_file = main_py_frame.filename
        else:
            caller_file = stack[2].filename  # past the current function and the __init__
        caller_folder = os.path.dirname(caller_file)
        default_config_path = os.path.join(caller_folder, "config.yaml")
        return default_config_path

    def _init_logger(self, logger) -> Any:
        """
        Initialize the tool logger.

        :param logger: A logger instance for logging purposes, or None 
            to create/use a default logger.
        :return: The tool logger
        """
        if logger is None:
            logger_config = self.config.get('logger')
            if logger_config:
                return Logger().configure(logger_config).get_logger()
            else:
                return Logger().get_logger()
        return logger

    def _validate_tool_manifest(self, manifest: dict) -> dict:
        """
        Validate the provided tool manifest against the Manifest model.

        :param manifest: The tool manifest dictionary to validate.
        :return: The validated manifest as a dictionary.
        :raises ValueError: If the manifest is invalid.
        """
        try:
            validated_manifest = self.Manifest(**manifest)
            return validated_manifest.model_dump()
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}") from e

    def __call__(self, func: Any) -> Any:
        """
        Make the AthonTool instance callable and set up the decorated function.

        :param func: The function to be decorated.
        :return: A wrapper function that incorporates additional logic
            around the invocation of the decorated function.
        """
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.logger.debug("Function call with AthonTool decorator")
            result = func(*args, **kwargs)
            return result

        self.function = func
        wrapper.athon_tool = self
        wrapper.invoke = self.invoke
        wrapper.get_manifest = self.get_manifest
        wrapper.run_app = self.run_app
        return wrapper


    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """
        Manually invoke the decorated function with the provided arguments.

        :return: The result of the function invocation.
        """
        try:
            self.logger.debug(f"Invoke function {self.config['tool']['function']}")
            return self.function(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error invoking function: {e}")
            raise


    def get_manifest(self, json_flag: bool = False) -> dict:
        """
        Retrieve the tool's manifest, optionally formatted as JSON.

        :param json_flag: Whether to return the manifest as JSON.
        :return: The tool's manifest.
        """
        try:
            self.logger.info("Create Manifest")
            manifest = copy.deepcopy(self.config["tool"])
            if not json_flag:
                manifest["function"] = self.function
            self.logger.debug(f"Tool's manifest: {manifest}")
            return manifest
        except Exception as e:
            self.logger.error(f"Not possible to create tool's manifest: {e}")
            raise


    def run_app(self, test: bool = False) -> Optional[Flask]:
        """
        Initialize and run a Flask web application based on the tool's settings.

        :param test: Whether to run the app in test mode.
        :return: The Flask app if in test mode, otherwise None.
        """
        try:
            self.logger.info('Starting the Tool APIs...')
            self.app = Flask(__name__)
            self._configure_routes(self.app)
            if test:
                return self.app
            webapp_config = self._get_webapp_config()
            self._start_flask_app(webapp_config)
            return None
        except Exception as e:
            self.logger.error(f"Not possible to start the tool's API: {e}")
            raise

    def _get_webapp_config(self) -> dict:
        """
        Retrieve the web application configuration from the tool's settings.

        :return: A dictionary with the web application configuration.
        """
        default_config = {'ip': '127.0.0.1'}
        return self.config.get('webapp', default_config)

    def _start_flask_app(self, config: dict) -> None:
        """
        Start the Flask application using the provided configuration.

        :param config: A dictionary with the configuration details.
        """
        app_run_args = {'host': config.get('ip', '127.0.0.1')}
        if 'port' in config:
            app_run_args['port'] = config['port']
        if 'ssh_cert' in config:
            app_run_args['ssl_context'] = config['ssh_cert']
        self.app.run(**app_run_args)

    def _configure_routes(self, app: Flask) -> None:
        """
        Configure the REST API routes for the Flask application.

        :param app: The Flask application instance.
        """
        self.logger.debug("Configuring REST API Routes")

        @app.route("/manifest")
        def get_manifest_json() -> Any:
            """
            Route to return the tool's manifest.

            :return: The tool's manifest as a JSON response.
            """
            return self._handle_manifest_request()

        @app.route("/tool", methods=['GET', 'POST'])
        def invoke_tool() -> Any:
            """
            Route to invoke the tool's main function.

            :return: The result of the tool invocation as a response.
            """
            return self._handle_tool_invocation()

        @app.route("/settings", methods=['GET'])
        def get_settings() -> Any:
            """
            Route to retrieve the current settings.

            :return: The current settings as a JSON response.
            """
            return jsonify(self._mask_sensitive_data(
                self._serialize_config(self.config),
                self.config["_sentitive_keys"])), 200

        @app.route("/settings", methods=['POST'])
        def set_settings() -> Any:
            """
            Route to update the current settings.

            :return: A JSON response indicating success or failure.
            """
            data = request.json
            self._update_existing_config(self.config, data)
            return jsonify({"status": "success", "message": "Settings updated."})

        @app.route("/files", methods=['POST'])
        def save_file() -> Any:
            """
            Route to save a file with a specified type.

            Expected JSON format:
            {
                "type": "CONFIG" or "PROMPT",
                "file_name": "example.txt",
                "file_content": "File content here..."
            }

            :return: A JSON response indicating success or failure.
            """
            data = request.json
            file_type = data.get("type")
            file_name = data.get("file_name")
            file_content = data.get("file_content")
            if file_type not in ["CONFIG", "PROMPT"]:
                return jsonify({"message": "Invalid file type specified"}), 400
            return self._handle_save_file(file_type, file_name, file_content)

    def _serialize_config(self, data):
        """
        Recursively traverse the data and replace non-serializable objects
        with a placeholder string.
        
        Args:
            data: The data structure to serialize (can be dict, list, etc.)
        
        Returns:
            A serialized version of the data with non-serializable objects replaced.
        """
        if isinstance(data, dict):
            return {key: self._serialize_config(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_config(element) for element in data]
        elif isinstance(data, (str, int, float, bool)) or data is None:
            return data
        else:
            # Replace non-serializable objects with a placeholder
            return f"$Object{{{data.__class__.__name__}}}"

    def _mask_sensitive_data(self, config, sensitive_keys):
        """
        Recursively mask sensitive keys in a nested configuration dictionary.

        : param config: The configuration dictionary to mask.
        : param sensitive_keys: Keys to mask in the configuration.
        :return: The configuration dictionary with sensitive values masked.
        """
        if isinstance(config, dict):
            masked_config = {}
            for key, value in config.items():
                if key in sensitive_keys:
                    masked_config[key] = "***MASKED***"
                else:
                    masked_config[key] = self._mask_sensitive_data(value, sensitive_keys)
            return masked_config
        if isinstance(config, list):
            # If the config contains lists, recursively apply masking to each item
            return [self._mask_sensitive_data(item, sensitive_keys) for item in config]
        return config

    def _handle_manifest_request(self) -> Any:
        """
        Handle the request to get the tool's manifest.

        :return: The tool's manifest as a JSON response.
        """
        try:
            manifest = self.get_manifest(json_flag=True)
            return jsonify(manifest)
        except Exception as e:  # pylint: disable=W0718
            self.logger.error("Failed to generate the tool's manifest")
            return str(e), 500  # Internal Server Error

    def _handle_tool_invocation(self) -> Any:
        """
        Handle the request to invoke the tool's main function.

        :return: The result of the tool invocation as a response.
        """
        try:
            params = self._extract_request_params(request)
            missing_params = [
                arg['name']
                for arg in self.config['tool']['arguments']
                if params[arg['name']] is None
            ]
            if missing_params:
                self.logger.error(f'Missing parameters: {missing_params}')
                # Bad Request
                return jsonify({'error': f'Missing parameters: {missing_params}'}), 400
            self.logger.debug(f"Function parameters: {params}")
            result = self.invoke(**params)
            return result
        except Exception as e:  # pylint: disable=W0718
            self.logger.error(f"An error occurred: {str(e)}")
            # Internal Server Error
            return jsonify({'error': 'An internal error occurred'}), 500

    def _extract_request_params(self, req: Any) -> dict:
        """
        Extract parameters from the request (GET or POST) based on the tool's argument configuration

        :param req: The request object.
        :return: A dictionary of the extracted parameters.
        """
        params = {}
        type_map = {'int': int, 'float': float, 'str': str, 'bool': bool}
        arguments_config = self.config['tool']['arguments']
        for arg in arguments_config:
            param_value = None
            if req.method == 'GET':
                param_value = req.args.get(
                    arg['name'], default=arg.get('default'), type=type_map.get(arg.get('type'))
                )
            elif req.method == 'POST':
                data = req.get_json()  # Assuming JSON is sent
                param_value = data.get(arg['name'], arg.get('default'))
            else:
                raise ValueError(f"Unsupported HTTP method: {req.method}")
            params[arg['name']] = param_value
        return params

    def _handle_save_file(self, file_type: str, file_name: str, file_content: str) -> dict:
        """
        Handle the saving of a file based on its type.

        :param file_type: The type of the file, e.g., "CONFIG" or "PROMPT".
        :param file_name: The name of the file to save.
        :param file_content: The content to save in the file.
        :return: A dictionary containing the status of the save operation and any error message.
        :raises ValueError: If an unsupported file type is provided.
        """
        # Map file types to their corresponding paths
        file_paths = {
            "CONFIG": self.config.get("_file_path"),
            "PROMPT": self.config.get("prompts", {}).get("environment")
        }
        file_path = file_paths.get(file_type)
        if file_path is None:
            raise ValueError(f"Unsupported file type: {file_type}")
        try:
            template_engine = TemplateEngine()
            template_engine.save(file_path, file_name, file_content)
            return jsonify({
                "status": "success",
                "message": f"File '{file_name}' saved successfully to '{file_path}'."
            })
        except Exception as e:  # pylint: disable=W0718
            self.logger.error(f"Failed to save file '{file_name}' to '{file_path}': {e}")
            return jsonify({"status": "failure", "error_message": str(e)})

    def _update_existing_config(self, config, data):
        """
        Update `config` with values from `data`, replacing the target directly 
        when a path is fully traversed. Supports paths like 'tool/interface/fields' or 
        'function/system_prompt', with the ability to replace the target
        with lists, dicts, or values.
        
        :param config: The original configuration dictionary to be updated.
        :param data: The dictionary containing updated values.
        """
        for key_path, value in data.items():
            keys = key_path.split('/')  # Split path by '/' to navigate into config
            target = config
            # Traverse the configuration to the target key
            for key in keys[:-1]:
                if key not in target:
                    # If a part of the path does not exist, create it as an empty dict
                    target[key] = {}
                target = target[key]
            # Replace the final key directly with the new value
            final_key = keys[-1]
            target[final_key] = self._resolve_nested_values(value)

    def _resolve_nested_values(self, value):
        """
        Recursively resolve values in nested dictionaries or lists.
        
        :param value: The original value.
        :return: The resolved value.
        """
        if isinstance(value, dict):
            # Resolve each item in the dictionary
            return {k: self._resolve_nested_values(v) for k, v in value.items()}
        if isinstance(value, list):
            # Resolve each item in the list
            return [self._resolve_nested_values(item) for item in value]
        # Resolve single values directly
        return self._resolve_value(value)

    def _resolve_value(self, value):
        """
        Resolve the value of config 
        
        :param value: The original value.
        :return: The resolved value.
        """
        if isinstance(value, str):
            if value.startswith("$ENV{") and value.endswith("}"):
                env_var = value[5:-1]
                return os.getenv(env_var, value)
        return value
