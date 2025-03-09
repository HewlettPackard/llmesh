#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utils functions for Meta-Prompting notebooks
"""

import os
import re
import json
import pandas as pd
import tiktoken
from langchain_core.messages import HumanMessage, SystemMessage
from athon.chat import PromptRender, ChatModel
from athon.system import Config
from self_serve_platform.system.file_cache import FileCache
# from src.meta_prompting.tool_manager import load_tools
# from src.meta_prompting.persona_agent import PersonaAgent
# from src.meta_prompting.agent_simulator import simluate_conversation


# Read config file in current folder
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.yaml')
config = Config(config_path).get_settings()
# Save  config variables
FILES_PATH = config['files']['path']
POLICY_FILE = FILES_PATH + config['files']['names']['policy']
# ROUTINE_FILE = FILES_PATH + config['files']['names']['routine']
# TEST_CASES_FILE = FILES_PATH + config['files']['names']['test_cases']
# TEST_RESULTS_FILE = FILES_PATH + config['files']['names']['test_results']
# META_PROMPTING_LLM_CONFIG = config['llms']['meta_prompting']
# AGENT_LLM_CONFIG = config['llms']['agent_persona']
# CUSTOMER_LLM_CONFIG = config['llms']['customer_persona']
# PROMPT_CONFIG = config['prompts']
# CACHE_CONFIG = config['cache']
# MAX_EVALUATION_LOOP = config['evaluation']['max_evaluations']
# MAX_IMPROVMENT_LOOP = config['evaluation']['max_improvments']
# MAX_TOKENS = config['evaluation']['max_tokens']
# MIN_ACCURACY = config['evaluation']['min_accuracy']
# TOOL_PATH = re.sub(r"[\\/]", ".", config['tools']['path'])
# TOOL_CLOSE = config['tools']['close_function']
# TOOL_MODULES = config['tools']['modules']
# TOOLS_OBJECTS, TOOLS = load_tools(TOOL_PATH, TOOL_MODULES)
# ENCODING = tiktoken.get_encoding("o200k_base")


def read_policy():
    "Read original policy file"
    return _read_file(POLICY_FILE)

# def load_prompt(prompt, args=None):
#     "Load the prompt"
#     prompt_render = PromptRender.create(PROMPT_CONFIG)
#     args = args or {}
#     result = prompt_render.load(prompt, **args)
#     if result.status == "success":
#         return result.content
#     raise ValueError(result.error_message)

# def read_test_dataframe():
#     "Read the Test Cases CSV file"
#     return _read_dataframe(TEST_CASES_FILE)

# def read_result_dataframe(version=0):
#     "Read the Test Cases result file"
#     file_path = _get_versioned_filepath(TEST_RESULTS_FILE, version)
#     return _read_dataframe(file_path)

# def write_result_dataframe(df, version=0):
#     "Write the Test Cases result file"
#     file_path = _get_versioned_filepath(TEST_RESULTS_FILE, version)
#     _write_dataframe(df, file_path)

# def get_routine(version = 0):
#     "Get the routine"
#     file_cache = FileCache(CACHE_CONFIG)
#     file_path = _get_versioned_filepath(ROUTINE_FILE, version)
#     if file_cache.is_cached(file_path):
#         return file_cache.load(file_path)
#     raise ValueError("Routine file no cached")

# def calculate_routine(system_prompt, policy, version = 0):
#     "Calculate routine using LLM and save in a file"
#     file_path = _get_versioned_filepath(ROUTINE_FILE, version)
#     file_cache = FileCache(CACHE_CONFIG)
#     if file_cache.is_cached(file_path):
#         routine = file_cache.load(file_path)
#     else:
#         routine = _generate_routine_with_llm(system_prompt, policy)
#         file_cache.save(file_path, routine)
#         _write_file(file_path, routine)
#     return routine

# def are_results_cached(version=0):
#     """
#     Checks if both the routine and test results files are cached.
#     """
#     file_cache = FileCache(CACHE_CONFIG)
#     # Check if routine file is cached
#     routine_file_path = _get_versioned_filepath(ROUTINE_FILE, version)
#     is_routine_cached = file_cache.is_cached(routine_file_path)
#     # Check if test results file exists
#     test_results_file_path = _get_versioned_filepath(TEST_RESULTS_FILE, version)
#     is_results_cached = os.path.exists(test_results_file_path)
#     return is_routine_cached and is_results_cached

# def _get_versioned_filepath(file_name, version):
#     base_name, ext = os.path.splitext(file_name)
#     return f"{base_name}_{version}{ext}"

# def evaluate_test_case(routine, test_row):
#     "Generate agent and customer and simulate their conversation"
#     personas = {
#         "customer": _create_customer_persona(test_row),
#         "agent": _create_agent_persona(routine),
#     }
#     return simluate_conversation(test_row, personas, TOOL_CLOSE, MAX_EVALUATION_LOOP)

# def generate_improve_messages(prev_results, routines, accuracies, system_prompt):
#     "Build a candidate message with the most recent eval (full table)"
#     pf = prev_results[-1].drop(columns=['Transcripts'])
#     new_eval_content = (
#         "## 3. Routine instructions:\n"
#         f"{routines[-1]}\n"
#         "## 4. Results table:\n"
#         f"{pf.to_json(orient='records')}\n"
#         "## 5. Evaluation history:\n"
#     )
#     if len(accuracies) > 1:
#         evals_history = _summarize_evals_history(routines, accuracies)
#     else:
#         evals_history = "Just 1 iteration done till now"
#     new_eval_content += f"{evals_history}\n"
#     return [
#         SystemMessage(content=system_prompt),
#         HumanMessage(new_eval_content)
#     ]

# def is_lower_than_max_tokens(messages):
#     "Check if we reach the max tokens"
#     return _num_tokens_from_messages(messages) <= MAX_TOKENS

# def improve_routine(messages, version = 1):
#     "Improve routine using LLM and save in a file"
#     file_path = _get_versioned_filepath(ROUTINE_FILE, version)
#     file_cache = FileCache(CACHE_CONFIG)
#     if file_cache.is_cached(file_path):
#         routine = file_cache.load(file_path)
#     else:
#         routine = _improve_routine_with_llm(messages)
#         file_cache.save(file_path, routine)
#         _write_file(file_path, routine)
#     return routine

def _read_file(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return file.read()

# def _generate_routine_with_llm(system_prompt, policy):
#     chat = ChatModel.create(META_PROMPTING_LLM_CONFIG)
#     prompts = [
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=f"POLICY:{policy}")
#     ]
#     result = chat.invoke(prompts)
#     if result.status == "success":
#         return result.content
#     raise ValueError(result.error_message)

# def _write_file(file_path, content):
#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(content)

# def _read_dataframe(file_path):
#     return pd.read_csv(file_path)

# def _write_dataframe(df, file_path):
#     df.to_csv(file_path, index=False)

# def _create_customer_persona(test_row):
#     details_dict = test_row.dropna().to_dict()
#     details_dict = {k: v for k, v in details_dict.items() if not k.startswith("Expected")}
#     system_prompt = load_prompt(
#         'customer_persona',
#         {
#             "details": details_dict,
#         }
#     )
#     return PersonaAgent(
#         CUSTOMER_LLM_CONFIG,
#         "user",
#         system_prompt
#     )

# def _create_agent_persona(routine):
#     system_prompt = load_prompt(
#         'agent_persona',
#         {
#             "routine": routine,
#         }
#     )
#     return PersonaAgent(
#         AGENT_LLM_CONFIG,
#         "assistant",
#         system_prompt,
#         TOOLS_OBJECTS
#     )

# def _num_tokens_from_messages(messages):
#     entire_input = ""
#     for message in messages:
#         entire_input += message.content + " "
#     tokens = ENCODING.encode(entire_input)
#     return len(tokens)

# def _improve_routine_with_llm(messages):
#     response_format = {
#         "name": "policy_output",
#         "schema": {
#             "type": "object",
#             "properties": {
#                 "final_answer": { "type": "string" }
#             },
#             "required": ["final_answer"],
#             "additionalProperties": False
#         },
#         "strict": True
#     }
#     chat = ChatModel.create(META_PROMPTING_LLM_CONFIG)
#     model = chat.get_model().model
#     json_model = model.bind(response_format={"type": "json_schema", "json_schema": response_format})
#     result = json_model.invoke(messages)
#     return json.loads(result.content)["final_answer"]

# def _summarize_evals_history(routines, accuracies):
#     system_prompt = load_prompt('evals_history')
#     user_prompt = (
#         "Accurancies:\n"
#         f"{accuracies}\n"
#         "Routines:\n"
#         f"{routines}\n"
#     )
#     chat = ChatModel.create(META_PROMPTING_LLM_CONFIG)
#     prompts = [
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=user_prompt)
#     ]
#     result = chat.invoke(prompts)
#     if result.status == "success":
#         return result.content
#     raise ValueError(result.error_message)
