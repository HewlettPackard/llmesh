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
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages.utils import get_buffer_string
from langchain_core.runnables.config import get_executor_for_config
from langchain_core.tools import tool
from libs.chat.model import ChatModel
from libs.chat.memory import ChatMemory
from libs.chat.message_manager import MessageManager
from libs.chat.prompt_render import PromptRender
from libs.rag.data_storage import DataStorage
from libs.rag.data_loader import DataLoader
from libs.rag.data_retriever import DataRetriever
from libs.core.config import Config
from libs.core.log import Logger


# Parse command-line arguments and start the application
PATH = 'examples/app_memory/'
CONFIG = Config(PATH+'config.yaml').get_settings()

MESSAGE_MEMORY_CONFIG = CONFIG["memories"]["messages"]
MESSAGE_MEMORY_KEY = CONFIG["memories"]["messages"]["memory_key"]
CORE_STORAGE_CONFIG = CONFIG["memories"]["core"]
RECALL_STORAGE_CONFIG = CONFIG["memories"]["recall"]
STORAGE_LOADER_CONFIG = CONFIG["memories"]["loader"]
STORAGE_RETRIEVER_CONFIG = CONFIG["memories"]["retriever"]
PROMPT_CONFIG = CONFIG["prompts"]
MODEL_CONFIG = CONFIG["llm"]

# Create Logger
logger = Logger().configure(CONFIG["logger"]).get_logger()
services = {
    "prompt_render": PromptRender.create(PROMPT_CONFIG),
    "chat_model": ChatModel.create(MODEL_CONFIG),
    "data_loader": DataLoader.create(STORAGE_LOADER_CONFIG),
    "data_retriever": DataRetriever.create(STORAGE_RETRIEVER_CONFIG)
}
memories = {}


def create_webapp(config):
    """
    Create the Flask application with its routes.
    It support 2 memories using LLM to decide where to
    store the messages.
    """
    logger.debug("Create Flask Web App")
    app = Flask(__name__)
    logger.debug("Configure Web App Routes")
    _init_memories()
    agent = _init_agent()
    _configure_routes(app, config, agent)
    return app

def _init_memories():
    memories["messages"] = _get_memory(MESSAGE_MEMORY_CONFIG)
    memories["core"] = _get_collection(CORE_STORAGE_CONFIG)
    _init_core_memory()
    memories["recall"] = _get_collection(RECALL_STORAGE_CONFIG)
    memories["last_recall"] = ""

def _get_memory(memory_config):
    chat_memory = ChatMemory.create(memory_config)
    result = chat_memory.get_memory()
    return result.memory

def _get_collection(storage_config):
    data_storage= DataStorage.create(storage_config)
    result = data_storage.get_collection()
    return result.collection

def _init_core_memory():
    memory = memories["core"]
    prompt = services["prompt_render"].load("project_info").content
    _store_memory(memory, prompt)

def _store_memory(memory, element):
    elements = [
        {
            "text": element,
            "metadata": {
                "timestamp": datetime.now(tz=timezone.utc),
            }
        }
    ]
    services["data_loader"].insert(memory, elements)

def _init_agent():
    tools = [
        save_core_memory,
        save_recall_memory,
        update_last_recall_memory
    ]
    llm = services['chat_model'].get_model()
    agent = create_tool_calling_agent(
        llm.model,
        tools,
        _get_agent_prompt())
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True)

def _get_agent_prompt():
    system_prompt = services["prompt_render"].load("store_memory").content
    logger.debug(f"Agent system prompt: '{system_prompt}'")
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

@tool
def save_core_memory(message: str) -> str:
    """Save the core memory"""
    _store_memory(memories["core"], message)
    return "Core memory updated"

@tool
def save_recall_memory(message: str) -> str:
    """Save the recall memory"""
    _store_memory(memories["recall"], memories["last_recall"])
    memories["last_recall"] = message
    return "Recall memory saved"

@tool
def update_last_recall_memory(message: str) -> str:
    """Update the last recall memory."""
    memories["last_recall"] += f" {message}"
    return "Recall memory updated"


def _configure_routes(app, config, agent):
    """
    Configures the routes for the Flask application.
    """

    @app.route('/load', methods=['POST'])
    def load_memory():
        "Route the load memory function"
        data = request.json
        if 'inputs'in data:
            result = _load_memories(data['inputs'])
            return jsonify(_convert_to_json(result)), 200
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
        return get_buffer_string(messages["chat_history"])

    def _fetch_core_memories(inputs):
        return _retrieve_from_collection(memories["core"], inputs)

    def _fetch_recall_memories(inputs):
        recall_memories = _retrieve_from_collection(memories["recall"], inputs)
        return [memories["last_recall"]] + recall_memories

    def _retrieve_from_collection(collection, query):
        result = services["data_retriever"].select(collection, query["input"])
        if result.status == "success" and result.elements:
            return [item["text"] for item in result.elements]
        return []

    def _get_related_memories(futures):
        messages = [
            SystemMessage(content = services["prompt_render"].load("load_memory").content),
            HumanMessage(content = _get_messages_prompt(futures))
        ]
        llm = services['chat_model'].get_model()
        result = llm.model.invoke(messages)
        return result.content

    def _get_messages_prompt(futures):
        result = services["prompt_render"].render(
            (
                "The messagges are:\n" 
                "{{ messages }}\n"
                "The memories are:\n"
                "{{ core_memories }}\n" 
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
            inputs = data['inputs']
            outputs = {"output": _remove_tags(data['outputs']['output'])}
            _store_messages(inputs, outputs)
            _store_memories(inputs, outputs)
            return jsonify({"message": "Memory saved"}), 200
        return jsonify({"error": "No message provided"}), 400

    def _remove_tags(text):
        text = re.sub(r'<code>.*?</code>', '', text, flags=re.DOTALL)
        text = re.sub(r'<img>.*?</img>', '', text, flags=re.DOTALL)
        return text

    def _store_messages(inputs, outputs):
        memories["messages"].save_context(inputs, outputs)

    def _store_memories(inputs, outputs):
        message = services["prompt_render"].render(
            (
                "Human wrote:\n" 
                "{{ input }}\n"
                "Assistant responded:\n"
                "{{ output }}\n" 
                "Last recall memory:\n"
                "{{ last_memory }}"
            ),
            input = inputs['input'],
            output = outputs['output'],
            last_memory = memories['last_recall']
        )
        result = agent.invoke({"input": message.content})
        logger.debug(f"Prompt generated {result['output']}")

    @app.route('/clear', methods=['POST'])
    def clear_memory():
        "Route the clear memory function"
        memories["messages"].clear()
        memories["last_recall"] = ""
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
