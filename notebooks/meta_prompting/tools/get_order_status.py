#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to get the order status.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class OrderStatusInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The unique identifier of the order to retrieve its status.")

def get_order_status(order_id: str) -> str:
    """Retrieve the status of an order given its order ID."""
    status = _fetch_order_status(order_id)
    return f"The order {order_id} status: {status}."

def _fetch_order_status(order_id: str) -> str:
    """
    Mock function to fetch the status of an order.
    In a real implementation, this would query a database or API.
    """
    mock_order_data: Dict[str, str] = {
        "11928": "Shipped",
        "22345": "Processing",
        "33456": "Delivered",
        "44567": "Cancelled"
    }
    return mock_order_data.get(order_id, "Order ID not found.")

OrderStatusTool = StructuredTool(
    name="get_order_status",
    func=get_order_status,
    args_schema=OrderStatusInput,
    description=(
        "Fetch the current status of an order given its order ID. "
        "Possible statuses: Processing, Shipped, Delivered, Cancelled."
    )
)


if __name__ == "__main__":
    TEST_ORDER_ID = "11928"
    response = get_order_status(TEST_ORDER_ID)
    print(response)
