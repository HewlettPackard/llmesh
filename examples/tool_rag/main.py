#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function to search info about 3GPP Standards for HPE Athonet LLM Platform. 
It uses advanced natural language processing techniques and integrates with OpenAI's 
models for document indexing, querying, and information retrieval. 
"""

import json
from sentence_transformers import CrossEncoder
from langchain.schema import HumanMessage, SystemMessage
from libs.chat.model import ChatModel
from libs.chat.prompt_render import PromptRender
from libs.rag.data_extractor import DataExtractor
from libs.rag.data_transformer import DataTransformer
from libs.rag.data_storage import DataStorage
from libs.rag.data_loader import DataLoader
from libs.rag.data_retriever import DataRetriever
from libs.system_services.tool_client import AthonTool
from libs.core.config import Config
from libs.core.log import Logger


config = Config('examples/tool_rag/config.yaml').get_settings()
logger = Logger().configure(config['logger']).get_logger()

LOAD = config["function"]["debug"]["load_files"]

EXTRACTOR_CONFIG = config["function"]["rag"]["extractor"]
TRANSFORMER_CONFIG = config["function"]["rag"]["transformer"]
ACTIONS_CONFIG = config["function"]["rag"]["actions"]
STORAGE_CONFIG = config["function"]["rag"]["storage"]
LOADER_CONFIG = config["function"]["rag"]["loader"]
RETRIEVER_CONFIG = config["function"]["rag"]["retriever"]
LLM_CONFIG = config["function"]["rag"]["llm_model"]
RERANK_MODEL = config["function"]["rag"]["rerank_model"]
SUMMARY_CHUNKS = config["function"]["rag"]["summary_chunks"]
PROMPT_CONFIG = config["prompts"]
PATH = config["data"]["path"]
FILES = config["data"]["files"]


@AthonTool(config, logger)
def telco_expert(query: str) -> str:
    """
    This function reads the telco standards, builds or use an vector store 
    from them, and then uses a query engine to find and return relevant 
    information to the input question.
    """
    collection = _get_collection()
    if LOAD:
        _load_files_into_db(collection)
    augment_query = _augment_query_generated(query)
    rag_results = _retrieve_from_collection(collection,augment_query)
    ordered_rag_results = _rerank_answers(augment_query, rag_results)
    summary_answer = _summary_answer(augment_query, ordered_rag_results)
    chunk_answer = _create_chunk_string(ordered_rag_results)
    return summary_answer + "\n\n" + chunk_answer

def _get_collection():
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

def _augment_query_generated(query):
    prompts = [
        SystemMessage(content = config["function"]["query_espantion"]),
        HumanMessage(content = query)
    ]
    content = _invoke_llm(prompts)
    logger.info(f"AUGMENTED QUESTION:\n{content}")
    return content

def _get_prompt(template):
    prompt = PromptRender.create(PROMPT_CONFIG)
    result = prompt.load(template)
    return result.content

def _invoke_llm(messages):
    chat = ChatModel.create(LLM_CONFIG)
    result = chat.invoke(messages)
    return result.content

def _retrieve_from_collection(collection, augment_query):
    data_retriever = DataRetriever.create(RETRIEVER_CONFIG)
    result = data_retriever.select(collection, augment_query)
    return result.elements

def _rerank_answers(query, elements, max_chunks=SUMMARY_CHUNKS):
    logger.debug("Rerank chunks")
    cross_encoder = CrossEncoder(RERANK_MODEL)
    pairs = [[query, doc["text"]] for doc in elements]
    scores = cross_encoder.predict(pairs)
    ordered_results = {
        "documents": [],
        "metadatas": [],
        "scores": []
    }
    ordered_indices = [
        index for index, score in sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )
    ]
    for o in ordered_indices[:max_chunks]:
        ordered_results['documents'].append(elements[o]["text"])
        ordered_results['metadatas'].append(elements[o]["metadata"])
        ordered_results['scores'].append(scores[o])
    return ordered_results

def _summary_answer(query, results):
    logger.debug("Summarize answer")
    information = "\n\n".join(results['documents'])
    prompts = [
        SystemMessage(content = _get_prompt("answer_summary")),
        HumanMessage(content = f"Question: {query}.\n Information: {information}")
    ]
    content = _invoke_llm(prompts)
    return content

def _create_chunk_string(results):
    result_list = []
    num_chunks = min(len(results['documents']), SUMMARY_CHUNKS)
    for i in range(num_chunks):
        result_dict = {
            "score": f"{results['scores'][i]:.2f}",
            "source": results['metadatas'][i]['filename'],
            "header": results['metadatas'][i]['header'],
            "chunk": results['documents'][i]
        }
        result_list.append(result_dict)
    # Convert the list of dictionaries to a JSON string
    json_string = json.dumps(result_list, indent=2)
    # To include the JSON string within <code> tags as shown in your example
    formatted_json_string = f"<code>{json_string}</code>"
    return formatted_json_string


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    It either prints the manifest or launches the web application
    based on the input parameter `local` : 
    - If True, the tool's manifest is printed.
    - If False, the web application is launched.
    """
    if local:
        return telco_expert.get_manifest()
    telco_expert.run_app()
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)
