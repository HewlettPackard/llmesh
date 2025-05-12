#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility functions for managing platform services environment variables.
"""

import os
from dotenv import load_dotenv

def set_services_env(llm_api_key: str = '', llm_model_name: str = '', serper_api_key: str = '', force: bool = False) -> tuple[str, str, str]:
    """
    Set up the environment for the chat model by creating or updating a .env file.
    Prompts the user for LLM_API_KEY and LLM_MODEL_NAME if not already set.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    env_file_path = os.path.join(data_dir, ".env")

    if os.path.exists(env_file_path):
        if not force:
            overwrite = input(f"{env_file_path} already exists. Overwrite? (y/n): ")
        else:
            overwrite = 'y'
        if overwrite.lower() == 'y':
            if not llm_api_key:
                llm_api_key = input("Enter LLM_API_KEY: ")
            if not llm_model_name:
                llm_model_name = input("Enter LLM_MODEL_NAME: ")
            if not serper_api_key:
                serper_api_key = input("Enter SERPER_API_KEY (value is ignored if not needed): ")
            with open(env_file_path, 'w') as env_file:
                env_file.write(f"LLM_API_KEY={llm_api_key}\n")
                env_file.write(f"LLM_MODEL_NAME={llm_model_name}\n")
                if serper_api_key:
                    env_file.write(f"SERPER_API_KEY={serper_api_key}\n")
            print(".env has been overwritten.")
        else:
            print("Keeping existing .env file.")
    else:
        if not llm_api_key:
            llm_api_key = input("Enter LLM_API_KEY: ")
        if not llm_model_name:
            llm_model_name = input("Enter LLM_MODEL_NAME: ")
        if not serper_api_key:
            serper_api_key = input("Enter SERPER_API_KEY (value is ignored if not needed): ")
        os.makedirs(data_dir, exist_ok=True)
        with open(env_file_path, 'w') as env_file:
            env_file.write(f"LLM_API_KEY={llm_api_key}\n")
            env_file.write(f"LLM_MODEL_NAME={llm_model_name}\n")
            if serper_api_key:
                env_file.write(f"SERPER_API_KEY={serper_api_key}\n")
        print(".env has been created in the data directory.")

    return get_services_env()


def get_services_env() -> tuple[str, str, str]:
    """
    Get the chat model environment variables.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    env_file_path = os.path.join(data_dir, ".env")
    load_dotenv(env_file_path)
    llm_api_key = os.getenv('LLM_API_KEY')
    if not llm_api_key:
        raise ValueError("API key is not set in environment variables.")
    llm_model_name = os.getenv('LLM_MODEL_NAME')
    if not llm_model_name:
        raise ValueError("Model name is not set in environment variables.")
    serper_api_key = os.getenv('SERPER_API_KEY', "")
    return llm_api_key, llm_model_name, serper_api_key
