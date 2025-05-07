#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides functions to transform elements' text into summaries
or QA pairs using a language model.
"""

import ast
from typing import List, Dict, Any
from tqdm import tqdm
from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from src.lib.services.chat.model import ChatModel


def transform_summary(
        llm_config: Any,
        system_prompt: str,
        action_prompt: str,
        transform_delimiters: List[str],
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Transform the text of elements into summaries using an LLM.

    :param llm_config: Configuration object for the LLM.
    :param system_prompt: Prompt for setting the context for the LLM.
    :param action_prompt: Prompt describing the action to perform.
    :param transform_delimiters: List of delimiters to remove from the output.
    :param elements: List of elements to transform.
    :return: List of transformed elements with summaries.
    """
    for element in tqdm(elements, desc="Processing elements"):
        summary = _transform_with_llm(
            llm_config,
            system_prompt,
            action_prompt,
            transform_delimiters,
            element['text']
        )
        element['metadata']['section'] = element['text']
        element['text'] = summary
        tqdm.write(f"Processed element: {element}")
    return elements

def transform_qa(
        llm_config: Any,
        system_prompt: str,
        action_prompt: str,
        transform_delimiters: List[str],
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    """
    Transform the text of elements into QA pairs using an LLM.

    :param llm_config: Configuration object for the LLM.
    :param system_prompt: Prompt for setting the context for the LLM.
    :param action_prompt: Prompt describing the action to perform.
    :param transform_delimiters: List of delimiters to remove from the output.
    :param elements: List of elements to transform.
    :return: List of transformed elements with QA pairs.
    """
    qa_list = []
    for element in tqdm(elements, desc="Processing elements"):
        qa_pairs_str = _transform_with_llm(
            llm_config,
            system_prompt,
            action_prompt,
            transform_delimiters,
            element['text']
        )
        qa_pairs = _convert_to_dict(qa_pairs_str)
        for qa_pair in qa_pairs:
            qa_element = {
                "text": qa_pair["question"],
                "metadata": {
                    **element['metadata'],
                    "answer": qa_pair["answer"],
                    "section": element['text']
                }
            }
            qa_list.append(qa_element)
        tqdm.write(f"Processed element: {element}")
    return qa_list

def _transform_with_llm(
        llm_config: Any,
        system_prompt: str,
        action_prompt: str,
        transform_delimiters: List[str],
        text: str
    ) -> str:
    """
    Use an LLM to transform the input text.

    :param llm_config: Configuration object for the LLM.
    :param system_prompt: Prompt for setting the context for the LLM.
    :param action_prompt: Prompt describing the action to perform.
    :param transform_delimiters: List of delimiters to remove from the output.
    :param text: Text to be transformed.
    :return: Transformed text.
    """
    messages = _create_messages(system_prompt, action_prompt, text)
    content = _invoke_llm(llm_config, messages)
    clean_content = _remove_delimiters(content, transform_delimiters)
    return clean_content

def _create_messages(system_prompt: str, action_prompt: str, text: str) -> List[BaseMessage]:
    """
    Create prompt messages for the LLM.

    :param system_prompt: Prompt for setting the context for the LLM.
    :param action_prompt: Prompt describing the action to perform.
    :param text: Text to be included in the user input prompt.
    :return: List of prompt messages.
    """
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"{action_prompt} \n**User Input:**\n ```{text}```")
    ]

def _invoke_llm(llm_config: Any, messages: List[BaseMessage]) -> str:
    """
    Invoke the LLM with the given messages.

    :param llm_config: Configuration object for the LLM.
    :param messages: List of messages to send to the LLM.
    :return: Content returned by the LLM.
    :raises RuntimeError: If the LLM invocation fails.
    """
    chat_model = ChatModel.create(llm_config)
    result = chat_model.invoke(messages)
    if result.status == "success":
        return result.content
    raise RuntimeError(f"LLM invocation failed with status: {result.status}")

def _remove_delimiters(content: str, delimiters: List[str]) -> str:
    """
    Remove specified delimiters from the content.

    :param content: Content from which to remove delimiters.
    :param delimiters: List of delimiters to remove.
    :return: Content without delimiters.
    """
    for delimiter in delimiters:
        content = content.replace(delimiter, "")
    return content

def _convert_to_dict(input_str: str) -> List[Dict[str, Any]]:
    """
    Convert a string representation of a list of dictionaries into an actual list of dictionaries.

    :param input_str: String representation of a list of dictionaries.
    :return: List of dictionaries.
    """
    real_dict = ast.literal_eval(input_str)
    return real_dict
