"""
Tools module containing custom function definitions for the voice agent.
"""

from .credit_card import (
    ELIGIBILITY_CHECK_TOOL,
    check_credit_card_eligibility,
    EligibilityResult,
)

__all__ = [
    "ELIGIBILITY_CHECK_TOOL",
    "check_credit_card_eligibility",
    "EligibilityResult",
]
