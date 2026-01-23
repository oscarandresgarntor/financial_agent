"""
Agent module containing Andrew's configuration and prompts.
"""

from .andrew import create_andrew_assistant, ANDREW_CONFIG
from .prompts import ANDREW_SYSTEM_PROMPT, ANDREW_FIRST_MESSAGE

__all__ = [
    "create_andrew_assistant",
    "ANDREW_CONFIG",
    "ANDREW_SYSTEM_PROMPT",
    "ANDREW_FIRST_MESSAGE",
]
