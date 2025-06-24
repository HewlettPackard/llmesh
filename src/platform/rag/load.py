#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function to load HPE documents for LAT-Mesh. 
"""

import os

from athon.rag import (
    DataExtractor,
    DataTransformer,
    DataStorage,
    DataLoader
)
from athon.system import (
    Config,
    Logger
)


# Load configuration
PATH = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(PATH, 'config.yaml')
config = Config(config_path).get_settings()
# Config settings
PATH = config["data"]["path"]
FILES = config["data"]["files"]
STORAGE_CONFIG = config["service"]["storage"]
EXTRACTOR_CONFIG = config["service"]["extractor"]
TRANSFORMER_CONFIG = config["service"]["transformer"]
ACTIONS_CONFIG = config["service"]["actions"]
LOADER_CONFIG = config["service"]["loader"]
RETRIEVER_CONFIG = config["service"]["retriever"]

# Create global objects
logger = Logger().configure(config['logger']).get_logger()


def load_files(reset=None):
    """
    Function to load files into the tool
    """
    collection = _get_collection(reset)
    _load_files_into_db(collection)

def _get_collection(reset=None):
    # Overwrite reset options
    if reset:
        STORAGE_CONFIG["reset"] = reset
    data_storage= DataStorage.create(STORAGE_CONFIG)
    result = data_storage.get_collection()
    return result.collection

def _load_files_into_db(collection):
    for file in FILES:
        logger.info(f"Load file {file['source']}")
        file_name = file["source"]
        file_path = PATH + file_name
        elements = _extract_file(file_path)
        transformed_elements = _transform_elements(elements)
        _load_elements(collection, transformed_elements)

def _extract_file(file_path):
    data_extractor = DataExtractor.create(EXTRACTOR_CONFIG)
    result = data_extractor.parse(file_path)
    return result.elements

def _transform_elements(elements):
    data_transformer = DataTransformer.create(TRANSFORMER_CONFIG)
    actions = ACTIONS_CONFIG
    result = data_transformer.process(actions, elements)
    return result.elements

def _load_elements(collection, elements):
    data_loader = DataLoader.create(LOADER_CONFIG)
    result = data_loader.insert(collection, elements)
    logger.debug(result.status)


if __name__ == "__main__":
    # Load documents.
    logger.info("Loading files into the system")
    load_files(reset=True)
