#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'Fantasia Genesis' tools

This file contains the tools related to the 'Fantasia Genesis' game
"""

import random
from datetime import datetime, timezone
from typing import Type, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from self_serve_platform.rag.data_storage import DataStorage
from self_serve_platform.rag.data_loader import DataLoader
from self_serve_platform.rag.data_retriever import DataRetriever
from self_serve_platform.system.config import Config
from self_serve_platform.system.log import Logger


config = Config('examples/app_games/config.yaml').get_settings()
logger = Logger().configure(config['logger']).get_logger()

WORLD_STORAGE_CONFIG = config["games"][1]["chat"]["world_db"]
HERO_STORAGE_CONFIG = config["games"][1]["chat"]["hero_db"]
LOADER_CONFIG = config["games"][1]["chat"]["loader"]
RETRIEVER_CONFIG = config["games"][1]["chat"]["retriever"]
RULES_PROMPT = config["games"][1]["chat"]["rules_prompt"]


class SaveToolInput(BaseModel):
    "Input schema for Save tools"

    information: Any = Field(..., description="Information to save")


class SaveWorld(BaseTool):
    "Class of the SaveWorld tool"

    name: str = "SaveWorld"
    description: str = "Tool to save the information related to the Fantasia World"
    args_schema: Type[BaseModel] = SaveToolInput

    def _run(self, information: Any) -> str:  # pylint: disable=W0221
        return _save_element(WORLD_STORAGE_CONFIG, information)


class SaveHero(BaseTool):
    "Class of the SaveHero tool"

    name: str = "SaveHero"
    description: str = "Tool to save the information related to the Fantasia Hero"
    args_schema: Type[BaseModel] = SaveToolInput

    def _run(self, information: Any) -> str:  # pylint: disable=W0221
        return _save_element(HERO_STORAGE_CONFIG, information)


class GetToolInput(BaseModel):
    "Input schema for Get tools"

    query: Any = Field(..., description="Query to use to retrieve information")


class GetWorld(BaseTool):
    "Class of the GetWorld tool"

    name: str = "GetWorld"
    description: str = "Tool to retrieve information related to the Fantasia World"
    args_schema: Type[BaseModel] = GetToolInput

    def _run(self, query: Any) -> str:  # pylint: disable=W0221
        return _retrieve_elements(WORLD_STORAGE_CONFIG, query)


class GetHero(BaseTool):
    "Class of the GetHero tool"

    name: str = "GetHero"
    description: str = "Tool to retrieve information related to the Fantasia Hero"
    args_schema: Type[BaseModel] = GetToolInput

    def _run(self, query: Any) -> str:  # pylint: disable=W0221
        return _retrieve_elements(HERO_STORAGE_CONFIG, query)


class GetRules(BaseTool):
    "Class of the GetHero tool"

    name: str = "FantasiaGenesisRules"
    description: str = "Tool to get the rules of the game"
    args_schema: Type[BaseModel] = GetToolInput

    def _run(self, query: Any) -> str:  # pylint: disable=W0221
        logger.debug(query)
        return RULES_PROMPT


class PlayToolInput(BaseModel):
    "Input schema for Play tool"

    difficulty: Any = Field(..., description="Level of difficulty")


class PlayLottery(BaseTool):
    "Class of the PlayLottery tool"

    name: str = "FantasiaGenesisLottery"
    description: str = "Tool to get the lottery result"
    args_schema: Type[BaseModel] = PlayToolInput

    def _run(self, difficulty: Any) -> str:  # pylint: disable=W0221
        logger.debug(difficulty)
        return random.randint(1, 100)


def _save_element(storage_config, element):
    collection = _get_collection(storage_config)
    text = _get_text("information", element)
    elements = [
        {
            "text": text,
            "metadata": {
                "timestamp": datetime.now(tz=timezone.utc),
            }
        }
    ]
    status = _load_elements(collection, elements)
    return status

def _get_text(key, element):
    if isinstance(element, str):
        text = element
    elif isinstance(element, dict) and key in element and "description" in element[key]:
        text = element[key]["description"]
    else:
        text = str(element)
    return text

def _retrieve_elements(storage_config, query):
    collection = _get_collection(storage_config)
    text = _get_text("query", query)
    elements = _retrieve_from_collection(collection, text)
    return elements

def _get_collection(storage_config):
    data_storage= DataStorage.create(storage_config)
    result = data_storage.get_collection()
    return result.collection

def _load_elements(collection, elements):
    data_loader = DataLoader.create(LOADER_CONFIG)
    result = data_loader.insert(collection, elements)
    return result.status

def _retrieve_from_collection(collection, query):
    data_retriever = DataRetriever.create(RETRIEVER_CONFIG)
    result = data_retriever.select(collection, query)
    return result.elements
