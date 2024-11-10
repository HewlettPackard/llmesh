#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web Chat Application with Reasoning Engine Integration

This script serves as the main entry point for the HPE Athonet LLM Platform's web application, 
integrating a reasoning engine to provide an interactive chat interface. The application 
utilizes Flask for web server capabilities, rendering a chat interface, and handling user input. 
The reasoning engine, created as a separate component, is responsible for processing user 
messages and generating intelligent responses.
"""

from flask import Flask, render_template, request, jsonify
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger
from self_serve_platform.chat.memory import ChatMemory
from self_serve_platform.chat.prompt_render import PromptRender
from self_serve_platform.system.tool_server import ToolDiscovery
from self_serve_platform.agents.tool_repository import ToolRepository
from self_serve_platform.agents.reasoning_engine import ReasoningEngine


# Supported Brands
BRANDS = ["athonet", "hpe"]
# Parse command-line arguments and start the application
PATH = 'examples/app_chatbot/'
CONFIG = Config(PATH+'config.yaml').get_settings()
# Create Logger
logger = Logger().configure(CONFIG['logger']).get_logger()


def create_webapp(config):
    """
    Create the Flask application with its routes and
    the reasoning engine.
    """
    logger.debug("Create Flask Web App")
    app = Flask(__name__, template_folder = "./html/templates", static_folder = "./html/static")
    logger.debug("Configure Web App Routes")
    _configure_routes(app, config)
    return app

def _configure_routes(app, config):
    """
    Configures the routes for the Flask application.
    """

    # Using a list to hold the selected project ID to allow modification within inner functions
    selected_project_id = [1]
    project_settings = {
        "tool_repository": _discover_project_tools(
            config["projects"],
            config["chat"]["tools"],
            config["chat"]["discovery"]),
        "projects": [],
        "engine": None
    }

    @app.route("/")
    def index():
        """
        Route to the index page.
        Clears the engine's chat history and renders the chat interface.
        """
        logger.debug("Load Home page")
        _clear_all_memories()
        _init_project(project_settings, config)
        project = project_settings["projects"][0]
        project_settings["engine"].set_tools(project["tools"])
        project_settings["engine"].set_memory(project["memory"])
        session_variables = _get_session_variables(config["webapp"]["brand"])
        result = render_template('index.html', **session_variables)
        return result


    def _clear_all_memories():
        for project in project_settings["projects"]:
            project["memory"].clear()

    def _get_session_variables(brand):
        if brand not in BRANDS:
            brand = "intelligen"
        session_variables = {}
        session_variables['theme'] = brand
        return session_variables

    @app.route("/message", methods=['POST'])
    def chat():
        """
        Route to handle chat requests.
        Accepts POST requests. Retrieves the user's message from the request,
        and passes it to the chat response generator.
        """
        try:
            data = request.get_json()  # Parse JSON data
            msg = data.get("msg")  # Get the 'msg' value from the JSON data
            logger.debug("Invoke LLM model")
            result = project_settings["engine"].run(msg)
            if result.status == "failure":
                raise RuntimeError(result.error_message)
            return result.completion
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Catch Exception running LLM or Tools")
            prompt = PromptRender.create(config["prompts"])
            result = prompt.load("chat_error_message", error = {str(e)})
            return result.content

    @app.route('/tools', methods=['GET'])
    def get_tools():
        """Endpoint to get a list of tools."""
        project_id = selected_project_id[0]
        for project in project_settings["projects"]:
            if project_id == project["id"]:
                project_name = project["project"]
                result = project_settings["tool_repository"].get_tools(
                    metadata_filter={"project": project_name})
                if result.status == "success":
                    filtered_tools = [
                        {"id": tool["metadata"]["id"], "name": tool["metadata"]["name"]}
                        for tool in result.tools
                    ]
                    return jsonify(filtered_tools)
        return jsonify([])

    @app.route('/tools/<int:tool_id>/fields', methods=['GET'])
    def get_tool_fields(tool_id):
        """Endpoint to get the fields for a specific tool."""
        result = project_settings["tool_repository"].get_tools(metadata_filter={"id": tool_id})
        if result.status == "success":
            return jsonify(result.tools[0]["metadata"]["interface"])
        return jsonify({})

    @app.route('/projects', methods=['GET'])
    def get_projects():
        """Endpoint to get a list of projects."""
        projects = []
        for project in project_settings["projects"]:
            projects.append({
                "id": project["id"],
                "name": project["project"]
            })
        return jsonify(projects)

    @app.route('/projects/<int:project_id>', methods=['GET'])
    def select_project(project_id):
        """Endpoint to select the project"""
        selected_project_id[0] = project_id
        for project in project_settings["projects"]:
            if project_id == project["id"]:
                project_name = project["project"]
                logger.debug(f"Project selected: {project_name}")
                project_settings["engine"].set_tools(project["tools"])
                project_settings["engine"].set_memory(project["memory"])
                response = {
                    "status": "success",
                    "selected_project": project_name
                }
                return jsonify(response)
        return jsonify({})

def _init_project(project_settings, config):
    project_settings["tool_repository"] = _discover_project_tools(
        config["projects"],
        config["chat"]["tools"],
        config["chat"]["discovery"],
        update=True)
    project_settings["projects"] = _create_project_manager(
        config["projects"],
        project_settings["tool_repository"])
    project_settings["engine"] = ReasoningEngine.create(config["chat"])

def _discover_project_tools(projects_config, tools_config, discovery_config,update=False):
    tool_repository = ToolRepository.create(tools_config)
    tool_discovery = ToolDiscovery(discovery_config)
    tool_id_counter = 1
    for project in projects_config:
        for tool in project["tools"]:
            tool_info = tool_discovery.discover_tool(tool)
            if tool_info:
                tool_metadata = {
                    "id": tool_id_counter,
                    "project": project["name"],
                    "name": tool_info["name"],
                    "interface": None
                }
                if tool_info.get("interface"):
                    tool_metadata["interface"] = tool_info["interface"]["fields"]
                if update:
                    tool_repository.update_tool(tool_info["name"], tool_info["tool"], tool_metadata)
                else:
                    tool_repository.add_tool(tool_info["tool"], tool_metadata)
                tool_id_counter += 1
    return tool_repository

def _create_project_manager(projects_config, tool_repository):
    project_manager = []
    project_id_counter = 1
    for project in projects_config:
        project_data = {
            "id": project_id_counter,
            "project": project["name"],
            "tools": _get_tools_names(tool_repository, project["name"]),
            "memory": _get_project_memory(project["memory"])
        }
        project_manager.append(project_data)
        project_id_counter += 1
    return project_manager

def _get_tools_names(tool_repository, project_name):
    result = tool_repository.get_tools(metadata_filter={"project": project_name})
    if result.status == "success":
        return [tool["metadata"]["name"] for tool in result.tools]
    return []

def _get_project_memory(memory_config):
    chat_memory = ChatMemory.create(memory_config)
    result = chat_memory.get_memory()
    if result.status == "success":
        return result.memory
    return None


def main():
    """
    Main function that serves as the entry point for the application.
    It create the Flask web app with all its routes and run it.
    """
    logger.info('Starting the Web App...')
    chat_bot = create_webapp(CONFIG)
    # Assuming self.settings['webapp'] is a dictionary with configuration settings
    webapp_config = CONFIG.get('webapp') or {'ip': '127.0.0.1'}
    # Run App using settings web app params
    app_run_args = {
        'host': webapp_config.get('ip', '127.0.0.1')
    }
    if 'port' in webapp_config:
        app_run_args['port'] = webapp_config['port']
    if 'ssh_cert' in webapp_config:
        app_run_args['ssl_context'] = webapp_config['ssh_cert']
    chat_bot.run(**app_run_args)


if __name__ == "__main__":
     # Run web application.
    main()
