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
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string
from langchain_core.runnables.config import (
    RunnableConfig,
    get_executor_for_config,
)

from datetime import datetime, timezone
from self_serve_platform.chat.model import ChatModel
from self_serve_platform.chat.memory import ChatMemory
from self_serve_platform.chat.message_manager import MessageManager
from self_serve_platform.chat.prompt_render import PromptRender
from self_serve_platform.rag.data_storage import DataStorage
from self_serve_platform.rag.data_loader import DataLoader
from self_serve_platform.rag.data_retriever import DataRetriever
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger


# Parse command-line arguments and start the application
PATH = 'examples/app_memory/'
CONFIG = Config(PATH+'config.yaml').get_settings()

MESSAGE_MEMORY_CONFIG = CONFIG["memories"]["messages"]
MESSAGE_MEMORY_KEY = CONFIG["memories"]["messages"]["memory_key"]
CORE_STORAGE_CONFIG = CONFIG["memories"]["core"]
REACALL_STORAGE_CONFIG = CONFIG["memories"]["recall"]
STORAGE_LOADER_CONFIG = CONFIG["memories"]["loader"]
STORAGE_RETRIEVER_CONFIG = CONFIG["memories"]["retriever"]
PROMPT_CONFIG = CONFIG["prompts"]
MODEL_CONFIG = CONFIG["llm"]

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
    memories = {
        "messages": _get_memory(MESSAGE_MEMORY_CONFIG),
        "core": _get_collection(CORE_STORAGE_CONFIG),
        "recall": _get_collection(REACALL_STORAGE_CONFIG),
    }
    services = {
        "prompt_render": PromptRender.create(PROMPT_CONFIG),
        "chat_model": ChatModel.create(MODEL_CONFIG),
        "data_loader": DataLoader.create(STORAGE_LOADER_CONFIG),
        "data_retriever": DataRetriever.create(STORAGE_RETRIEVER_CONFIG)
    }
    _init_core_memory(services, memories["core"])
    _store_memory(
        services,
        memories["core"],
        services["prompt_render"].load("project_info").content)
    _configure_routes(app, config, memories, services)
    return app

def _get_memory(memory_config):
    chat_memory = ChatMemory.create(memory_config)
    result = chat_memory.get_memory()
    return result.memory

def _get_collection(storage_config):
    data_storage= DataStorage.create(storage_config)
    result = data_storage.get_collection()
    return result.collection

def _init_core_memory(services, memory):
    prompt = services["prompt_render"].load("project_info").content
    _store_memory(services, memory, prompt)

def _store_memory(services, memory, element):
    elements = [
        {
            "text": element,
            "metadata": {
                "timestamp": datetime.now(tz=timezone.utc),
            }
        }
    ]
    services["data_loader"].insert(memory, elements)

def _configure_routes(app, config, memories, services):
    """
    Configures the routes for the Flask application.
    """

    current_memory = ""

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
        with get_executor_for_config(config) as executor:
            futures = [
                executor.submit(_fetch_messages, inputs),
                executor.submit(_fetch_core_memories, inputs),
                executor.submit(_fetch_recall_memories, inputs),
            ]
            related_memories = _get_related_memories(futures)
        return {MESSAGE_MEMORY_KEY: [AIMessage(content=related_memories)]}

    def _fetch_messages(inputs):
        messages = memories["messages"].load_memory_variables(inputs)
        return [get_buffer_string(message) for message in messages]

    def _fetch_core_memories(inputs):
        return _retrieve_from_collection(memories["core"], inputs)

    def _fetch_recall_memories(inputs):
        recall_memories = _retrieve_from_collection(memories["reacall"], inputs)
        return [current_memory] + recall_memories

    def _retrieve_from_collection(collection, query):
        convo_str = get_buffer_string(query)
        result = services["data_retriever"].select(collection, convo_str)
        if result.status == "success" and result.elements:
            return [item["text"] for item in result.elements]
        return []

    def _get_related_memories(futures):
        messages = [
            SystemMessage(content = services["prompt_render"].load("load_memory").content),
            HumanMessage(content = _get_messages_prompt(futures))
        ]
        result = services["chat_model"].invoke(messages)
        return result.content

    def _get_messages_prompt(futures):
        result = services["prompt_render"].render(
            (
                "The messagges are" 
                "{{ messages }}"
                "The memories are"
                "{{ core_memories }}" 
                "{{ recall_memories }}" 
            ),
            messages = futures[0].result(),
            core_memories = futures[1].result(),
            recall_memories = futures[2].result()
        )
        return result.content

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
            memories["messages"].save_context(inputs, data['outputs'])



            return jsonify({"message": "Memory saved"}), 200
        return jsonify({"error": "No message provided"}), 400

    def _convert_to_messages(prompts):
        messages = MessageManager.create(config["messages"])
        result = messages.convert_to_messages(prompts)
        return result.prompts
