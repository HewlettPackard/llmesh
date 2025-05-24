#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to cancel an order before shipment.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class CancelOrderInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The order ID to cancel.")

def cancel_order(order_id: str) -> str:
    """Cancel an order if it is still in processing."""
    data = _fetch_order_data()
    if order_id in data and data[order_id] == "Processing":
        return f"Order {order_id} has been successfully cancelled."
    return (
        f"Order {order_id} cannot be cancelled." 
        f"Current status: {data.get(order_id, 'Order ID not found.')}"
    )

def _fetch_order_data() -> Dict[str, str]:
    """
    Mock function to simulate order statuses.
    """
    return {
        "55566": "Processing",
        "77788": "Shipped"
    }

CancelOrderTool = StructuredTool(
    name="cancel_order",
    func=cancel_order,
    args_schema=CancelOrderInput,
    description="Cancel an order before it has been shipped."
)


if __name__ == "__main__":
    response = cancel_order("55566")
    print(response)
