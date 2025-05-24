#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to handle customer complaints and disputes.
"""

from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class HandleComplaintInput(BaseModel):
    """Tool input schema"""
    complaint_details: str = Field(
        ...,
        description="Details of the customer complaint.")

def handle_complaint(complaint_details: str) -> str:
    """Address and resolve customer disputes based on the provided complaint details."""
    return f"Complaint received: {complaint_details}. Your case ID is CMP003."

HandleComplaintTool = StructuredTool(
    name="handle_complaint",
    func=handle_complaint,
    args_schema=HandleComplaintInput,
    description="Log and address customer complaints or disputes."
)

if __name__ == "__main__":
    response = handle_complaint("Received a damaged item in order 99001")
    print(response)
