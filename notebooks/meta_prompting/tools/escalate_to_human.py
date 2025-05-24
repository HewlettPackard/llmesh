#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Commerce Tool to escalate an issue to a human representative.
"""

from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class EscalateToHumanInput(BaseModel):
    """Tool input schema"""
    issue_details: str = Field(
        ...,
        description="Details of the issue requiring human intervention."
    )

def escalate_to_human(issue_details: str) -> str:
    """Escalate an issue to a human customer support representative."""
    return (
        f"Your issue has been escalated to a human agent:"
        f" {issue_details}. An agent will contact you shortly."
    )

EscalateToHumanTool = StructuredTool(
    name="escalate_to_human",
    func=escalate_to_human,
    args_schema=EscalateToHumanInput,
    description="Escalate an issue to a human representative for further assistance."
)


if __name__ == "__main__":
    response = escalate_to_human("Customer is unsatisfied with the resolution for order 11234")
    print(response)
