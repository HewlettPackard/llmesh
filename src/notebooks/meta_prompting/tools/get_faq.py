#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to retrieve automated responses for frequently asked questions.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

class GetFAQResponseInput(BaseModel):
    """Tool input schema"""
    faq_topic: str = Field(
        ...,
        description="The FAQ topic to retrieve information about.")

def get_faq_response(faq_topic: str) -> str:
    """Retrieve automated responses for frequently asked questions."""
    data = _fetch_faq_responses()
    return data.get(faq_topic.lower(), "FAQ topic not found. Please try another keyword.")

def _fetch_faq_responses() -> Dict[str, str]:
    """
    Mock function to simulate FAQ responses.
    """
    return {
        "returns": "You can return items within 30 days of purchase.",
        "refunds": "Refunds are processed within 5-7 business days.",
        "shipping": "Standard shipping takes 3-5 business days."
    }

GetFAQResponseTool = StructuredTool(
    name="get_faq_response",
    func=get_faq_response,
    args_schema=GetFAQResponseInput,
    description=(
        "Retrieve automated responses for frequently asked questions"
        " (e.g., returns, refunds, shipping)."
    )
)


if __name__ == "__main__":
    response = get_faq_response("refunds")
    print(response)
