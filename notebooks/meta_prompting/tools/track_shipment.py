#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to track shipment details of an order.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class TrackShipmentInput(BaseModel):
    """Tool input schema"""
    order_id: str = Field(
        ...,
        description="The order ID for tracking information.")

def track_shipment(order_id: str) -> str:
    """Retrieve tracking details for a shipped order."""
    data = _fetch_tracking_data()
    return (
        f"Order {order_id} tracking status:" 
        f"{data.get(order_id, 'No tracking information available.')}"
    )

def _fetch_tracking_data() -> Dict[str, str]:
    """
    Mock function to simulate shipment tracking data.
    """
    return {
        "99900": "In transit - Expected delivery in 2 days",
        "11223": "Delivered - Signed by recipient"
    }

TrackShipmentTool = StructuredTool(
    name="track_shipment",
    func=track_shipment,
    args_schema=TrackShipmentInput,
    description="Fetch tracking details for a shipped order."
)


if __name__ == "__main__":
    response = track_shipment("99900")
    print(response)
