#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to process a refund request for an order.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class ProcessRefundInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The order ID for the refund request.")
    refund_amount: str = Field(
        ...,
        description="The amount to be refunded.")

def process_refund(order_id: str, refund_amount: str) -> str:
    """Issue a refund for a given order ID and amount."""
    data = _fetch_refund_data()
    if order_id in data and data[order_id] == "Approved":
        return f"Refund of ${refund_amount} has been successfully processed for order {order_id}."
    return (
        f"Refund request denied for order {order_id}." 
        f"Reason: {data.get(order_id, 'Order ID not found.')}"
    )

def _fetch_refund_data() -> Dict[str, str]:
    """
    Mock function to simulate refund processing.
    """
    return {
        "77889": "Approved",
        "99001": "Denied - Payment method restriction"
    }

ProcessRefundTool = StructuredTool(
    name="process_refund",
    func=process_refund,
    args_schema=ProcessRefundInput,
    description="Process a refund request for an order."
)


if __name__ == "__main__":
    response = process_refund("77889", "49.99")
    print(response)
