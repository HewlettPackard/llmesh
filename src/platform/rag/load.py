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
    try:
        collection = _get_collection(reset)
        _load_files_into_db(collection)
        logger.info("File loading process completed.")
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Failed to load files: {e}")

def _get_collection(reset=None):
    # Overwrite reset options
    if reset:
        STORAGE_CONFIG["reset"] = True
    try:
        data_storage = DataStorage.create(STORAGE_CONFIG)
        result = data_storage.get_collection()
        return result.collection
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Error getting collection from storage: {e}")
        raise

def _load_files_into_db(collection):
    if not FILES:
        logger.warning("No files specified in configuration.")
        return
    for file in FILES:
        file_name = file.get("source")
        if not file_name:
            logger.warning("Missing 'source' key in file config.")
            continue
        file_path = os.path.join(PATH, file_name)
        logger.info(f"Loading file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue
        try:
            elements = _extract_file(file_path)
            transformed_elements = _transform_elements(elements)
            _load_elements(collection, transformed_elements)
        except Exception as e:  # pylint: disable=W0718
            logger.exception(f"Error processing file {file_path}: {e}")

def _extract_file(file_path):
    try:
        data_extractor = DataExtractor.create(EXTRACTOR_CONFIG)
        result = data_extractor.parse(file_path)
        return result.elements or []
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Error extracting file {file_path}: {e}")
        return []

def _transform_elements(elements):
    if not elements:
        logger.warning("No elements to transform.")
        return []
    try:
        data_transformer = DataTransformer.create(TRANSFORMER_CONFIG)
        actions = ACTIONS_CONFIG
        result = data_transformer.process(actions, elements)
        return result.elements or []
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Error transforming elements: {e}")
        return []

def _load_elements(collection, elements):
    if not elements:
        logger.warning("No elements to load into collection.")
        return
    try:
        data_loader = DataLoader.create(LOADER_CONFIG)
        result = data_loader.insert(collection, elements)
        logger.debug(f"Insert status: {result.status}")
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Error loading elements into collection: {e}")


if __name__ == "__main__":
    # Load documents.
    logger.info("Loading files into the system")
    load_files(reset=True)
