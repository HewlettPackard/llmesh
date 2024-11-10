#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Memory App

This script serves as the main entry point for the memory web application, 
providing functionalities to configure the memory and its endpoints. 
The application utilizes Flask for web server capabilities, rendering the admin interface, 
and handling user input. 
"""

import re
from flask import Flask, request, jsonify
from langchain.schema import HumanMessage
from self_serve_platform.chat.model import ChatModel
from self_serve_platform.chat.memory import ChatMemory
from self_serve_platform.chat.message_manager import MessageManager
from self_serve_platform.chat.prompt_render import PromptRender
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger


# Parse command-line arguments and start the application
PATH = 'examples/app_memory/'
CONFIG = Config(PATH+'config.yaml').get_settings()
UPDATE_SYSTEM_MEMORY = False
# Create Logger
logger = Logger().configure(CONFIG["logger"]).get_logger()


def create_webapp(config):
    """
    Create the Flask application with its routes.
    It support 2 memories using LLM to decide where to
    store the messages.
    """
    logger.debug("Create Flask Web App")
    app = Flask(__name__)
    logger.debug("Configure Web App Routes")
    personal_memory = _setup_memory(config["memory"]["personal"])
    project_memory = _setup_memory(config["memory"]["project"])
    if config["memory"]["personal"]["memory_key"] == config["memory"]["project"]["memory_key"]:
        memory_key = config["memory"]["personal"]["memory_key"]
        _configure_routes(app, personal_memory, project_memory, memory_key, config)
    return app

def _setup_memory(config):
    chat_memory = ChatMemory.create(config)
    result = chat_memory.get_memory()
    return result.memory

def _configure_routes(app, personal_memory, project_memory, memory_key, config):
    """
    Configures the routes for the Flask application.
    """

    @app.route('/load', methods=['POST'])
    def load_memory():
        "Route the load memory function"
        data = request.json
        if 'inputs'in data:
            result = _load_memories(data['inputs'])
            result = _convert_to_json(result)
            return jsonify(result), 200
        return jsonify({"error": "No message provided"}), 400

    def _load_memories(inputs):
        personal_result = personal_memory.load_memory_variables(inputs)
        project_result = project_memory.load_memory_variables(inputs)
        if not personal_result[memory_key]:
            if project_result[memory_key]:
                personal_result[memory_key].append(project_result[memory_key][0])
        elif UPDATE_SYSTEM_MEMORY:
            # Update System Memory with project memory
            personal_result[memory_key][0] = project_result[memory_key][0]
        return personal_result

    def _convert_to_json(prompts):
        messages = MessageManager.create(config["messages"])
        result = messages.convert_to_strings(prompts)
        return result.prompts

    @app.route('/store', methods=['POST'])
    def store_memory():
        "Route the store memory function"
        data = request.json
        if 'inputs' in data and 'outputs' in data:
            inputs = _convert_to_messages(data['inputs'])
            memory_type = _get_memory_type(inputs, memory_key)
            # Clean text among tags code and img
            cleaned_output = _remove_tags(data['outputs']['output'])
            data['outputs']['output'] = cleaned_output
            if memory_type == "project":
                logger.debug("Saved project memory")
                project_memory.save_context(inputs, data['outputs'])
            else:
                logger.debug("Saved personal memory")
                personal_memory.save_context(inputs, data['outputs'])
            return jsonify({"message": "Memory saved"}), 200
        return jsonify({"error": "No message provided"}), 400

    def _convert_to_messages(prompts):
        messages = MessageManager.create(config["messages"])
        result = messages.convert_to_messages(prompts)
        return result.prompts

    def _get_memory_type(inputs, memory_key):
        project_description = ""
        if inputs[memory_key]:
            project_description = inputs[memory_key][0].content
        prompt = _render_prompt(project_description, inputs["input"])
        memory_type = _reason_with_llm(prompt)
        return memory_type

    def _remove_tags(text):
        text = re.sub(r'<code>.*?</code>', '', text, flags=re.DOTALL)
        text = re.sub(r'<img>.*?</img>', '', text, flags=re.DOTALL)
        return text

    def _render_prompt(project_description, input_message):
        prompt = PromptRender.create(config["prompts"])
        result = prompt.load(
            "select_memory",
            project_description = project_description,
            input_message = input_message)
        return result.content

    def _reason_with_llm(prompt):
        messages = [HumanMessage(content = prompt)]
        content = _invoke_llm(messages)
        return _remove_delimeters(content, "```")

    def _invoke_llm(messages):
        chat = ChatModel.create(config["llm"])
        result = chat.invoke(messages)
        return result.content

    def _remove_delimeters(content, delimeters):
        content = content.replace(" ", "")
        content = content.replace("\t", "")
        content = content.replace("\n", "")
        for delimeter in delimeters:
            content = content.replace(delimeter, "")
        return content

    @app.route('/clear', methods=['POST'])
    def clear_memory():
        "Route the clear memory function"
        personal_memory.clear()
        project_memory.clear()
        project_memory.buffer = config["memory"]["project"]["buffer"]
        return jsonify({"message": "Memory cleared"}), 200


if __name__ == '__main__':
    # Start the application
    logger.info('Starting the Web App...')
    memapp = create_webapp(CONFIG)
    app_run_args = {
        'host': CONFIG["webapp"].get('ip', '127.0.0.1')
    }
    if 'port' in CONFIG["webapp"]:
        app_run_args['port'] = CONFIG["webapp"]['port']
    if 'ssh_cert' in CONFIG["webapp"]:
        app_run_args['ssl_context'] = CONFIG["webapp"]['ssh_cert']
    memapp.run(**app_run_args)
