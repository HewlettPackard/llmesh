#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to initiate a return request for an order.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class InitiateReturnInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The order ID for return request.")
    reason: str = Field(
        ...,
        description="Reason for returning the item.")

def initiate_return(order_id: str, reason: str) -> str:
    """Process a return request for an order."""
    data = _fetch_return_eligibility()
    if order_id in data and data[order_id] == "Eligible":
        return f"Return for order {order_id} has been initiated for the following reason: {reason}."
    return (
        f"Order {order_id} cannot be returned."
        f"Reason: {data.get(order_id, 'Order ID not found.')}"
    )

def _fetch_return_eligibility() -> Dict[str, str]:
    """
    Mock function to simulate return eligibility check.
    """
    return {
        "33445": "Eligible",
        "55667": "Not eligible - Return window expired"
    }

InitiateReturnTool = StructuredTool(
    name="initiate_return",
    func=initiate_return,
    args_schema=InitiateReturnInput,
    description="Process a return request for an order."
)


if __name__ == "__main__":
    response = initiate_return("33445", "Defective item")
    print(response)
