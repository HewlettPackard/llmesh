#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to retrieve a customer's past orders.
"""

from typing import Dict, List
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class CustomerOrderHistoryInput(BaseModel):
    """Tool input schema"""
    customer_id: str = Field(
        ...,
        description="The unique identifier of the customer.")

def get_customer_order_history(customer_id: str) -> str:
    """Retrieve past orders for a given customer ID."""
    data = _fetch_customer_orders()
    return (
        f"Order history for {customer_id}:"
        f"{', '.join(data.get(customer_id, ['No order history available.']))}"
    )

def _fetch_customer_orders() -> Dict[str, List[str]]:
    """
    Mock function to simulate retrieval of customer order history.
    """
    return {
        "CUST001": ["Order 11234 - Delivered", "Order 22345 - Processing"],
        "CUST002": ["Order 33456 - Shipped"]
    }

CustomerOrderHistoryTool = StructuredTool(
    name="get_customer_order_history",
    func=get_customer_order_history,
    args_schema=CustomerOrderHistoryInput,
    description="Retrieve a customer’s past orders."
)


if __name__ == "__main__":
    response = get_customer_order_history("CUST001")
    print(response)
