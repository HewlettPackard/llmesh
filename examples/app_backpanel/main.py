#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin Panel for Tool Management

This script serves as the main entry point for the admin panel web application, 
providing functionalities to select a tool, view tool details, and change tool settings. 
The application utilizes Flask for web server capabilities, rendering the admin interface, 
and handling user input. 

The application is designed to be modular with route configurations separated 
from the main application logic. 
This modularity facilitates ease of maintenance and scalability.
"""

from flask import Flask, render_template, request, jsonify
from self_serve_platform.system.tool_server import ToolDiscovery
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger
from examples.app_backpanel.tool_manager.prompt import PromptTool
from examples.app_backpanel.tool_manager.rag import RagTool


# Supported Brands
BRANDS = ["athonet", "hpe"]
# Tool classes
TOOL_CLASSES = {
    'PromptTool': PromptTool,
    'RagTool': RagTool,
    # Add other tool types and their classes here
}
# Parse command-line arguments and start the application
PATH = 'examples/app_backpanel/'
CONFIG = Config(PATH+'config.yaml', replace_placeholders=False).get_settings()
# Create Logger
logger = Logger().configure(CONFIG['logger']).get_logger()


def create_webapp(config):
    """
    Create the Flask application with its routes.
    """
    logger.debug("Create Flask Web App")
    app = Flask(
        __name__,
        template_folder="./html/templates",
        static_folder="./html/static"
    )
    logger.debug("Configure Web App Routes")
    _configure_routes(app, config)
    return app

def _configure_routes(app, config):
    """
    Configures the routes for the Flask application.
    """

    tools = {"loaded": []}

    @app.route("/")
    def index():
        """
        Route to the index page.
        Renders the tool selection interface.
        """
        tools["loaded"] = _load_tools(config)
        logger.debug("Load Home page")
        session_variables = _get_session_variables(config["webapp"]["brand"])
        result = render_template('index.html', **session_variables)
        return result

    def _get_session_variables(brand):
        if brand not in BRANDS:
            brand = "intelligen"
        session_variables = {}
        session_variables['theme'] = brand
        return session_variables

    @app.route("/tools", methods=["GET"])
    def get_tools():
        """Endpoint to get a list of tools."""   
        tool_list = []
        for tool in tools["loaded"] :
            tool_elem = {
                "id": tool["id"],
                "name": tool["name"],
                "type": tool["type"]
            }
            tool_list.append(tool_elem)
        return jsonify(tool_list)

    @app.route("/tools/<int:tool_id>", methods=["GET"])
    def get_tool_details(tool_id):
        """Endpoint to get the details of a specific tool."""
        tool_info = _get_tool_info(tool_id)
        if tool_info:
            tool = _create_tool(tool_info)
            if tool:
                tool_info = tool.get_settings()
                if tool_info:
                    return jsonify(tool_info)
                return jsonify({"error": "Tool settings not found"}), 404
            return jsonify({"error": f"Unsupported tool type '{tool_info.get('type')}'"}), 400
        return jsonify({"error": "Tool not found"}), 404

    def _get_tool_info(tool_id):
        return next((tool for tool in tools["loaded"]  if tool['id'] == tool_id), None)

    @app.route("/tools/<int:tool_id>/reset", methods=["POST"])
    def reset_to_default(tool_id):
        """Endpoint to get the details of a specific tool."""
        tool_entry = _get_tool_info(tool_id)
        if tool_entry:
            tool = _create_tool(tool_entry)
            if tool:
                tool_info = tool.set_settings(None, True)
                if tool_info:
                    return jsonify(tool_info)
                return jsonify({"error": "Not possible to restore default settings"}), 404
            return jsonify({"error": f"Unsupported tool type '{tool_entry.get('type')}'"}), 400
        return jsonify({"error": "Tool not found"}), 404

    @app.route("/tools/<int:tool_id>/prompt", methods=["POST"])
    def improve_system_prompt(tool_id):
        """Endpoint to get the details of a specific tool."""
        tool_entry = _get_tool_info(tool_id)
        if tool_entry:
            tool = _create_tool(tool_entry)
            if tool:
                # Get the JSON data from the request
                system_prompt = request.json
                improved_system_prompt = tool.improve_prompt(system_prompt['prompt'])
                if improved_system_prompt:
                    return jsonify(improved_system_prompt)
                return jsonify({"error": "Not possible to restore default settings"}), 404
            return jsonify({"error": f"Unsupported tool type '{tool_entry.get('type')}'"}), 400
        return jsonify({"error": "Tool not found"}), 404

    @app.route("/tools/<int:tool_id>/settings", methods=["POST"])
    def apply_tool_settings(tool_id):
        """Endpoint to update the settings of a specific tool."""
        tool_entry = _get_tool_info(tool_id)
        if tool_entry:
            tool = _create_tool(tool_entry)
            if tool:
                # Get the JSON data from the request
                settings = request.json
                logger.debug(f"Saving settings for tool {tool_id}:")
                response = tool.apply_settings(settings) # add response
                if response:
                    return jsonify(response), 200
                return jsonify({"error": "Not possible to apply settings"}), 404
        logger.error("Not possible to apply settings: tool not found")
        return jsonify({"error": "Tool not found"}), 404

def _load_tools(config):
    validated_tools = []
    for index, tool_entry in enumerate(config.get('tools', [])):
        try:
            base_url = tool_entry.get('base_url')
            if base_url:
                try:
                    tool_settings = _fetch_tool_settings(base_url)
                except Exception as e:  # pylint: disable=W0718
                    logger.error(f"Failed to fetch settings from {base_url}: {e}")
                    continue  # Skip to the next tool if fetching settings fails
                if tool_settings:
                    try:
                        tool_info = _validate_tool_settings(index, tool_entry, tool_settings)
                        if tool_info:
                            validated_tools.append(tool_info)
                        else:
                            logger.error(f"Validation failed for tool at {base_url}.")
                    except Exception as e:  # pylint: disable=W0718
                        logger.error(f"Failed to validate settings for tool at {base_url}: {e}")
                else:
                    logger.error(f"No config file found at {base_url} at index {index}.")
            else:
                logger.error(f"Tool entry at index {index} is missing 'base_url'. Skipping.")
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"An unexpected error occurred at index {index}: {e}")
    return validated_tools

def _fetch_tool_settings(base_url):
    tool_discovery = ToolDiscovery(CONFIG["function"]["discovery"])
    return tool_discovery.get_settings(base_url)

def _validate_tool_settings(index, tool_entry, tool_settings):
    tool = _create_tool(tool_entry, True)
    if not tool:
        return None
    return tool.validate(index, tool_settings)

def _create_tool(tool_info, partial=False):
    tool_type = tool_info.get('type')
    tool_class = TOOL_CLASSES.get(tool_type, partial)
    if not tool_class:
        logger.error(f"Unsupported tool type '{tool_type}'.")
        return None
    return tool_class(tool_info, partial)

def main():
    """
    Main function that serves as the entry point for the application.
    It create the Flask web app with all its routes and run it.
    """
    logger.info('Starting the Web App...')
    admin_panel = create_webapp(CONFIG)
    app_run_args = {
        'host': CONFIG["webapp"].get('ip', '127.0.0.1')
    }
    if 'port' in CONFIG["webapp"]:
        app_run_args['port'] = CONFIG["webapp"]['port']
    if 'ssh_cert' in CONFIG["webapp"]:
        app_run_args['ssl_context'] = CONFIG["webapp"]['ssh_cert']
    admin_panel.run(**app_run_args)


if __name__ == "__main__":
     # Run web application.
    main()
