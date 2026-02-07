"""
Credit card eligibility check tool for the Voice AI Agent.

This module provides the function definition for Vapi and the
business logic for checking customer eligibility.
"""

from enum import Enum
from pydantic import BaseModel


class EligibilityStatus(str, Enum):
    """Possible eligibility outcomes."""
    ELIGIBLE = "eligible"
    REVIEW_REQUIRED = "review_required"
    NOT_ELIGIBLE = "not_eligible"


class EligibilityResult(BaseModel):
    """Result of an eligibility check."""
    status: EligibilityStatus
    message: str
    recommended_action: str
    annual_income: float
    has_existing_credit: bool | None = None


# Tool definition for Vapi
ELIGIBILITY_CHECK_TOOL = {
    "type": "function",
    "function": {
        "name": "check_credit_card_eligibility",
        "description": "Check if a customer is eligible for the Bank-travel credit card based on their income and credit history",
        "parameters": {
            "type": "object",
            "properties": {
                "annual_income": {
                    "type": "number",
                    "description": "Customer's annual income in USD"
                },
                "has_existing_credit": {
                    "type": "boolean",
                    "description": "Whether the customer has existing credit history (credit cards, loans, etc.)"
                }
            },
            "required": ["annual_income"]
        }
    }
}


def check_credit_card_eligibility(
    annual_income: float,
    has_existing_credit: bool | None = None
) -> EligibilityResult:
    """
    Check if a customer is eligible for the Bank-travel credit card.

    Eligibility Logic (Mock):
    - Income >= $25,000 → Eligible
    - Income < $25,000 but has credit history → Review required
    - Income < $25,000, no credit history → Not eligible

    Args:
        annual_income: Customer's annual income in USD
        has_existing_credit: Whether customer has existing credit history

    Returns:
        EligibilityResult with status, message, and recommended action
    """
    # Minimum income threshold for automatic approval
    MIN_INCOME_THRESHOLD = 25000

    if annual_income >= MIN_INCOME_THRESHOLD:
        return EligibilityResult(
            status=EligibilityStatus.ELIGIBLE,
            message="Great news! Based on the information provided, you appear to be eligible for the Bank-travel credit card.",
            recommended_action="You can proceed with the application. Would you like me to help you get started?",
            annual_income=annual_income,
            has_existing_credit=has_existing_credit,
        )

    elif has_existing_credit is True:
        return EligibilityResult(
            status=EligibilityStatus.REVIEW_REQUIRED,
            message="Based on your income and credit history, your application would need a quick review by our team.",
            recommended_action="I can submit your application for review. Our team typically responds within 1-2 business days. Would you like to proceed?",
            annual_income=annual_income,
            has_existing_credit=has_existing_credit,
        )

    else:
        return EligibilityResult(
            status=EligibilityStatus.NOT_ELIGIBLE,
            message="Unfortunately, based on the information provided, you don't currently qualify for this credit card.",
            recommended_action="I'd recommend our Starter Credit Card, which is designed to help build credit history. Can I transfer you to a human representative who can tell you more about that option?",
            annual_income=annual_income,
            has_existing_credit=has_existing_credit,
        )


def format_eligibility_response(result: EligibilityResult) -> str:
    """
    Format the eligibility result for voice response.

    Args:
        result: The eligibility check result

    Returns:
        A natural language response suitable for voice
    """
    return f"{result.message} {result.recommended_action}"
