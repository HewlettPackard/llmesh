#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ecommerce Tool to close a case
"""

from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class CaseResolutionInput(BaseModel):
    "Tool input schema"
    order_id: str = Field(
        ...,
        description = "The ID of the order"
    )

def close_case(order_id: str) -> str:
    "Tool function"
    return f"Close case for order: {order_id}"

CaseResolutionTool = StructuredTool(
    name = "close_case",
    func = close_case,
    args_schema = CaseResolutionInput,
    description = (
        "Tool to close a case."
    )
)

if __name__ == "__main__":
    response = close_case("11923")
    print(response)
