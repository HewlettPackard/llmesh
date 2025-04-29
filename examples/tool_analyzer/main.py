#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides functionality to read temperature data from a CSV dataset,
utilize a Large Language Model (LLM) to generate Python code for data analysis
and visualization, execute the generated code, and save the resulting plot as an
image. The image is then encoded as text for transmission.
It utilizes the AthonTool decorator for configuration and logging setup.
"""

import io
import base64
import json
from tqdm import tqdm
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for non-GUI rendering
import matplotlib.pyplot as plt  # pylint: disable=W0611,C0413
from langchain.schema import HumanMessage, SystemMessage  # pylint: disable=C0413
from libs.chat.model import ChatModel  # pylint: disable=C0413
from libs.chat.prompt_render import PromptRender  # pylint: disable=C0413
from libs.system_services.tool_client import AthonTool  # pylint: disable=C0413
from libs.core.config import Config  # pylint: disable=C0413
from libs.core.log import Logger  # pylint: disable=C0413


# Parse command-line arguments and start the application
config = Config('examples/tool_analyzer/config.yaml').get_settings()
# Config settings
LLM_CONFIG = config["function"]["llm"]
PROMPT_CONFIG = config["prompts"]
FILE_NAME = config["function"]["file_name"]
FILE_PATH = config["function"]["file_path"] + FILE_NAME
PLOT_FUNCTION = config["function"]["plot_function"]
CHUNKSIZE = config["function"]["chunksize"]
LOG_CONFIG = config['logger']
# Create Logger
logger = Logger().configure(LOG_CONFIG).get_logger()

# Read the file in chunks
FILE_INDEX = 1
DATA_FRAME = pd.DataFrame()
for chunk in tqdm(pd.read_csv(FILE_PATH, chunksize=CHUNKSIZE), desc="Processing chunks"):
    DATA_FRAME = pd.concat([DATA_FRAME, chunk])


@AthonTool(config, logger)
def temperature_analyzer(query: str) -> str:
    """
    Analyzes the temperature dataset and generates a plot using a 
    Large Language Model (LLM) to generate Python code  based on the specified
    analysis request. 
    """
    try:
        code = _create_analysis_code(query)
        plot = _create_plot_by_code(code)
        response = _format_response(plot, code)
        return response
    except Exception as e:  # pylint: disable=W0718
        return str(e)

def _create_analysis_code(query):
    prompts = [
        SystemMessage(content = _get_prompt("system_prompt")),
        HumanMessage(content = _get_analysis_prompt(query))
    ]
    content = _invoke_llm(prompts)
    logger.info(f"PYTHON CODE:\n{content}")
    return _clean_generated_code(content)

def _get_prompt(template):
    prompt = PromptRender.create(PROMPT_CONFIG)
    result = prompt.load(template)
    return result.content

def _get_analysis_prompt(query):
    df_head = DATA_FRAME.head(5)
    df_columns = DATA_FRAME.columns.to_list()
    prompt = PromptRender.create(PROMPT_CONFIG)
    result = prompt.load(
        "analysis_request",
        plot_function = PLOT_FUNCTION,
        df_head = df_head,
        df_columns = df_columns,
        analysis_query = query)
    return result.content

def _invoke_llm(messages):
    chat = ChatModel.create(LLM_CONFIG)
    result = chat.invoke(messages)
    return result.content

def _clean_generated_code(code):
    # Remove the first line and the last line
    code_lines = code.split('\n')[1:-1]
    return "\n".join(code_lines)

def _create_plot_by_code(code_str):
    # Execute the cleaned code string to define the function
    exec(code_str)  # pylint: disable=W0122
    # Check if the function is defined
    if '_create_plot' not in locals():
        logger.error("_create_plot function is not defined.")
    # Call the function
    plot_function = locals()[PLOT_FUNCTION]
    plot = plot_function(DATA_FRAME)
    return plot

def _format_response(plot, code):
    img = io.BytesIO()
    plot.savefig(img, format='png')
    img.seek(0)
    image_string = "<img>" + base64.b64encode(img.read()).decode('utf-8') + "</img>"
    code_json = {
        "dataset": FILE_NAME,
        "code": code,
    }
    code_string = "<code>" + json.dumps(code_json, indent=2) + "</code>"
    response_string = image_string + "\n\n" + code_string.replace("\\n", "\n")
    return response_string


def main(local=True):
    """
    Main function that serves as the entry point for the application.
    It either prints the manifest or launches the web application
    based on the input parameter `local` : 
    - If True, the tool's manifest is printed.
    - If False, the web application is launched.
    """
    if local:
        return temperature_analyzer.get_manifest()
    temperature_analyzer.run_app()
    return None


if __name__ == "__main__":
    # Run in web application mode.
    main(False)
