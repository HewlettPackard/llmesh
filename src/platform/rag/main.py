#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module initializes an agentic tool of the platform rag service.
It utilizes the AthonTool decorator for configuration and logging setup.
"""

import os
import json
from sentence_transformers import CrossEncoder
from langchain.schema import HumanMessage, SystemMessage
from athon.chat import (
    ChatModel,
    PromptRender
)
from athon.rag import (
    DataStorage,
    DataRetriever
)
from athon.system import (
    AthonTool,
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
PROMPT_CONFIG = config["prompts"]
QUERY_EXPANTION_PROMPT = config["service"]["query_espantion"]
QUERY_HYDE_PROMPT = config["service"]["query_hyde"]
LLM_CONFIG = config["service"]["llm"]
STORAGE_CONFIG = config["service"]["storage"]
EXTRACTOR_CONFIG = config["service"]["extractor"]
TRANSFORMER_CONFIG = config["service"]["transformer"]
ACTIONS_CONFIG = config["service"]["actions"]
LOADER_CONFIG = config["service"]["loader"]
RERANK_MODEL = config["service"]["rerank"]["model"]
SUMMARY_CHUNKS = config["service"]["rerank"]["summary_chunks"]
RETRIEVER_CONFIG = config["service"]["retriever"]

# Create global objects
logger = Logger().configure(config['logger']).get_logger()


@AthonTool(config, logger)
def retrieve(query: str, augemntation: str="espantion") -> str:
    """
    This function reads the documentations, builds or use an vector store 
    from them, and then uses a query engine to find and return relevant 
    information to the input question.
    """
    collection = _get_collection()
    augment_query = _augment_query_generated(query, augemntation)
    rag_results = _retrieve_from_collection(collection,augment_query)
    ordered_rag_results = _rerank_answers(augment_query, rag_results)
    summary_answer = _summary_answer(augment_query, ordered_rag_results)
    chunk_answer = _create_chunk_string(ordered_rag_results)
    return summary_answer + "\n\n" + chunk_answer

def _get_collection():
    data_storage= DataStorage.create(STORAGE_CONFIG)
    result = data_storage.get_collection()
    return result.collection

def _augment_query_generated(query, augemntation):
    if augemntation == "hyde":
        system_prompt = QUERY_HYDE_PROMPT
    else:
        system_prompt = QUERY_EXPANTION_PROMPT
    prompts = [
        SystemMessage(content = system_prompt),
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
        index for index, _ in sorted(
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
        return retrieve.get_manifest()
    retrieve.run_app()
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)
