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
QUERY_EXPANTION_PROMPT = config["service"]["query_expantion"]
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
def retrieve(query: str, augmentation: str = "expansion", rerank: bool = True) -> str:
    """
    This function reads the documentations, builds or uses a vector store 
    from them, and then uses a query engine to find and return relevant 
    information to the input question.
    """
    try:
        collection = _get_collection()
        augment_query = _augment_query_generated(query, augmentation)
        rag_results = _retrieve_from_collection(collection, augment_query)
        ordered_rag_results = _rerank_answers(augment_query, rag_results, rerank)
        summary_answer = _summary_answer(augment_query, ordered_rag_results)
        chunk_answer = _create_chunk_string(ordered_rag_results)
        return summary_answer + "\n\n" + chunk_answer
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Unexpected error in retrieve(): {e}")
        return "An error occurred during processing."

def _get_collection():
    try:
        data_storage = DataStorage.create(STORAGE_CONFIG)
        result = data_storage.get_collection()
        return result.collection
    except Exception as e:  # pylint: disable=W0718
        logger.exception(f"Error initializing collection: {e}")
        return None

def _augment_query_generated(query, augmentation):
    prompts_map = {
        "hyde": QUERY_HYDE_PROMPT,
        "expansion": QUERY_EXPANTION_PROMPT
    }
    system_prompt = prompts_map.get(augmentation)
    if not system_prompt:
        return query
    prompts = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    try:
        content = _invoke_llm(prompts)
        logger.info(f"AUGMENTED QUESTION:\n{content}")
        return content
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error during query augmentation: {e}")
        return query

def _get_prompt(template):
    try:
        prompt = PromptRender.create(PROMPT_CONFIG)
        result = prompt.load(template)
        return result.content
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error loading prompt template '{template}': {e}")
        return ""

def _invoke_llm(messages):
    try:
        chat = ChatModel.create(LLM_CONFIG)
        result = chat.invoke(messages)
        return result.content
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error invoking LLM: {e}")
        return ""


def _retrieve_from_collection(collection, augment_query):
    try:
        data_retriever = DataRetriever.create(RETRIEVER_CONFIG)
        result = data_retriever.select(collection, augment_query)
        return result.elements or []
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error retrieving from collection: {e}")
        return []

def _rerank_answers(query, elements, rerank, max_chunks=SUMMARY_CHUNKS):
    ordered_results = {
        "documents": [],
        "metadatas": [],
        "scores": []
    }
    if not elements:
        logger.warning("No elements provided for reranking.")
        return ordered_results
    if rerank:
        logger.debug("Reranking chunks...")
        cross_encoder = CrossEncoder(RERANK_MODEL)
        pairs = [[query, doc["text"]] for doc in elements]
        try:
            scores = cross_encoder.predict(pairs)
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"Error during reranking: {e}")
            return ordered_results
        ordered_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )
        for idx in ordered_indices[:max_chunks]:
            ordered_results["documents"].append(elements[idx]["text"])
            ordered_results["metadatas"].append(elements[idx]["metadata"])
            ordered_results["scores"].append(scores[idx])
    else:
        logger.debug("Skipping reranking, returning top elements as-is.")
        for element in elements[:max_chunks]:
            ordered_results["documents"].append(element["text"])
            ordered_results["metadatas"].append(element["metadata"])
            ordered_results["scores"].append(None)  # No score available
    return ordered_results

def _summary_answer(query, results):
    logger.debug("Summarize answer")
    try:
        information = "\n\n".join(results.get("documents", []))
        prompts = [
            SystemMessage(content=_get_prompt("answer_summary")),
            HumanMessage(content=f"Question: {query}.\nInformation: {information}")
        ]
        return _invoke_llm(prompts)
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error summarizing answer: {e}")
        return "Summary generation failed."

def _create_chunk_string(results):
    result_list = []
    num_chunks = min(len(results['documents']), SUMMARY_CHUNKS)
    for i in range(num_chunks):
        result_dict = _build_result_dict(results, i)
        result_list.append(result_dict)
    try:
        json_string = json.dumps(result_list, indent=2)
        return f"```json\n{json_string}\n```"
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error formatting JSON chunk string: {e}")
        return "Error creating chunk summary."

def _build_result_dict(results, i):
    """Safely builds a result dictionary from ranked results."""
    try:
        score = results.get('scores', [None])[i]
        score_str = f"{score:.2f}" if score is not None else "N/A"
    except (IndexError, TypeError, ValueError):
        score_str = "N/A"
    metadatas = results.get('metadatas', [])
    documents = results.get('documents', [])
    metadata = metadatas[i] if i < len(metadatas) else {}
    document = documents[i] if i < len(documents) else ""
    return {
        "score": score_str,
        "source": metadata.get('filename', 'Unknown'),
        "header": metadata.get('header', 'No header'),
        "chunk": document or "No content"
    }


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
