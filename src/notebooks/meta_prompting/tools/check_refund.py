#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to check refund eligibility for an order.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class CheckRefundEligibilityInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The order ID to check refund eligibility.")

def check_refund_eligibility(order_id: str) -> str:
    """Verify if an order qualifies for a refund."""
    data = _fetch_refund_eligibility()
    return (
        f"Order {order_id} refund status:"
        f"{data.get(order_id, 'Order ID not found.')}"
    )

def _fetch_refund_eligibility() -> Dict[str, str]:
    """
    Mock function to simulate refund eligibility check.
    """
    return {
        "55667": "Eligible for refund",
        "77889": "Not eligible - Refund policy expired"
    }

CheckRefundEligibilityTool = StructuredTool(
    name="check_refund_eligibility",
    func=check_refund_eligibility,
    args_schema=CheckRefundEligibilityInput,
    description="Verify if an order qualifies for a refund."
)


if __name__ == "__main__":
    response = check_refund_eligibility("55667")
    print(response)
