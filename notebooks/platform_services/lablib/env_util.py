#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility functions for managing platform services environment variables.
"""

from dotenv import load_dotenv
from pathlib import Path
import os

def load_environment():
    """
    Configure the environment by loading the .env file.
    This function will look for a .env file in the current directory or the project root.
    """
    # Load environment variables from a .env file in either the current directory or the project root
    notebook_dir = Path(os.getcwd()).parent
    project_root = Path(os.getcwd()).parent.parent

    dotenv_path = notebook_dir / '.env'
    if not load_dotenv(dotenv_path):
        dotenv_path = project_root / '.env'
        if not load_dotenv(dotenv_path):
            print("No .env file found in %s or %s.", project_root / '.env', notebook_dir / '.env')
        else:
            print("Environment variables loaded from: %s", dotenv_path)
    else:
        print("Environment variables loaded from: %s", dotenv_path)


def get_services_env() -> tuple[str, str, str]:
    """
    Get the chat model environment variables.
    """
    load_environment()
    llm_api_key = os.getenv('OPENAI_API_KEY')
    if not llm_api_key:
        raise ValueError("API key is not set in environment variables.")
    llm_model_name = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini-2024-07-18')
    if not llm_model_name:
        raise ValueError("Model name is not set in environment variables.")
    serper_api_key = os.getenv('SERPER_API_KEY', "")
    return llm_api_key, llm_model_name, serper_api_key
