#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulate agent personas conversation to evaluate meta-prompt
"""

import math
import json
from typing import List, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from src.lib.package.athon.chat import ChatModel


class PersonaAgent:
    """
    A class that simulates an agent persona using an LLM model,
    a system prompt (routine), and an ongoing message transcript.
    """
    def __init__(self, llm_config, role: str, system_prompt: str, tools: Any = None):
        """
        Initialize the persona agent.
        
        :param llm_config: Configuration for the LLM (model name, parameters, etc.)
        :param role: The persoma role.
        :param system_prompt: The system prompt with the info of the personas.
        :param use_tools: Whether the agent should have access to the tools.
        """
        self.system_prompt = system_prompt
        self.role = role
        model = self._get_model(llm_config)
        if tools:
            self.tools = tools
            self.model = model.bind_tools(tools)
        else:
            self.tools = None
            self.model = model

    def _get_model(self, llm_config):
        chat = ChatModel.create(llm_config)
        result = chat.get_model()
        if result.status == "success":
            return result.model
        raise ValueError(result.error_message)

    def respond(self, transcript: List) -> Any:
        """
        Takes the user’s input, appends it to the transcript,
        and gets a response from the agent LLM.
        
        :param transcript: Thelist of messages.
        :return: The agent’s response.
        """
        response = self._invoke_model(transcript)
        self._update_transcript(transcript, response)
        return response

    def _invoke_model(self, transcript):
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        messages.extend(transcript)
        response = self.model.invoke(messages)
        response.role = self.role
        return response

    def _update_transcript(self, transcript, response):
        if response.role == "user":
            human_message = HumanMessage(
                content=response.content,
                role=response.role,
                response_metadata=getattr(response, "response_metadata", None)
            )
            transcript.append(human_message)
        else:
            transcript.append(response)
            self._call_tool(transcript, response)

    def _call_tool(self, transcript, response):
        tool_calls = response.tool_calls
        if not tool_calls:
            return
        for tool_call in tool_calls:
            function_name = tool_call["name"]
            arguments = tool_call["args"]
            # Find the corresponding tool
            tool = next((t for t in self.tools if t.name == function_name), None)
            if not tool:
                error_message = f"No tool named '{function_name}' found."
                tool_response = ToolMessage(
                    role="tool",
                    content=error_message,
                    tool_call_id=tool_call["id"]
                )
                transcript.append(tool_response)
                continue
            try:
                # Run the tool and capture its result
                tool_result = tool.run(tool_input={**arguments})
                # Ensure tool_result is always a string
                if isinstance(tool_result, (dict, list)):
                    tool_result_str = json.dumps(tool_result, indent=2)
                else:  # Convert other object types explicitly
                    tool_result_str = str(tool_result)
            except Exception as e:  # pylint: disable=W0718
                # If there's any error while running the tool, capture its message
                tool_result_str = f"Error occurred while running the tool: {e}"
            # Create the tool response message
            tool_response = ToolMessage(
                role="tool",
                content=tool_result_str,
                tool_call_id=tool_call["id"]
            )
            # Append the response to the transcript
            transcript.append(tool_response)


def simluate_conversation(test_row, personas, close_function = 'close_case', max_loop = 10):
    "Evaluate the agents conversation"
    # Prepare initial result data
    record = {
        'Request': test_row['Request'],
        'Context': test_row['Context'],
        'Expected Function': _safe_str(test_row['Expected Function']),
        'Expected Inputs': json.loads(test_row['Expected Inputs']),
        'Actual Function': None,
        'Actual Inputs': None,
        'Is Correct': False,
        'Transcripts': [HumanMessage(content=test_row['Request'], role="user")]
    }
    try:
        loop_count = 0
        while True:
            loop_count += 1
            if loop_count > max_loop:
                break
            # Call agent_response with the current transcript, routine, model
            response = personas["agent"].respond(record["Transcripts"])
            tool_calls = response.tool_calls
            if not tool_calls:
                # Simulate customer response
                personas["customer"].respond(record["Transcripts"])
                continue
            function_name = tool_calls[-1]["name"]
            if function_name == close_function:
                break
            if function_name:
                record["Actual Function"] = function_name
                record["Actual Inputs"] = tool_calls[-1]["args"]
        record["Transcripts"] = _format_transcript(record["Transcripts"])
        record["Is Correct"] = (
            (record["Actual Function"] == record["Expected Function"]) and
            (str(record["Actual Inputs"]) == str(record["Expected Inputs"]))
        )
    except Exception as e:  # pylint: disable=W0718
        print(f"Error simulating the conversation: {e}")
    return record

def _safe_str(value):
    return "" if (isinstance(value, float) and math.isnan(value)) else str(value)

def _format_transcript(messages):
    formatted_text = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "* User"
        elif isinstance(message, AIMessage):
            role = "* Assistant"
        elif isinstance(message, ToolMessage):
            role = "* Tool"
        else:
            role = "* Unknown"
        formatted_text.append(f"{role}: {message.content}")
    return "\n".join(formatted_text)
