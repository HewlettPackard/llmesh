#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to modify an existing order.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class ModifyOrderInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The order ID to modify.")
    modification_details: str = Field(
        ...,
        description="Details of the requested modification.")

def modify_order(order_id: str, modification_details: str) -> str:
    """Modify an order given its order ID and modification details."""
    data = _fetch_order_data()
    if order_id in data and data[order_id]["status"] == "Processing":
        return f"Order {order_id} modification successful: {modification_details}."
    return (
        f"Order {order_id} cannot be modified." 
        f"Current status: {data.get(order_id, {}).get('status', 'Order ID not found.')}."
    )

def _fetch_order_data() -> Dict[str, Dict[str, str]]:
    """
    Mock function to simulate order modifications.
    """
    return {
        "11122": {"status": "Processing", "modification": "Address Updated"},
        "33344": {"status": "Shipped", "modification": "Cannot be modified"}
    }

ModifyOrderTool = StructuredTool(
    name="modify_order",
    func=modify_order,
    args_schema=ModifyOrderInput,
    description="Modify an existing order, such as updating the shipping address or item quantity."
)


if __name__ == "__main__":
    response = modify_order("11122", "Change shipping address to 456 Elm St")
    print(response)
