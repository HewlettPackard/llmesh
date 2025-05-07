#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to update customer account details.
"""

from typing import Dict
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class UpdateCustomerAccountInput(BaseModel):
    """Tool input schema"""
    customer_id: str = Field(
        ...,
        description="The customer ID whose account is to be updated.")
    update_type: str = Field(
        ...,
        description="Type of update (e.g., email, password, phone number).")
    new_value: str = Field(
        ...,
        description="New value for the update field.")

def update_customer_account(customer_id: str, update_type: str, new_value: str) -> str:
    """Modify customer account details."""
    data = _fetch_customer_data()
    if customer_id in data:
        return f"Customer {customer_id} {update_type} has been updated to {new_value}."
    return "Customer ID not found."

def _fetch_customer_data() -> Dict[str, Dict[str, str]]:
    """
    Mock function to simulate customer account updates.
    """
    return {
        "CUST001": {"name": "John Doe", "email": "johndoe@example.com"},
        "CUST002": {"name": "Jane Smith", "email": "janesmith@example.com"}
    }

UpdateCustomerAccountTool = StructuredTool(
    name="update_customer_account",
    func=update_customer_account,
    args_schema=UpdateCustomerAccountInput,
    description="Modify customer account details such as email, password, or phone number."
)


if __name__ == "__main__":
    response = update_customer_account("CUST001", "email", "newemail@example.com")
    print(response)
