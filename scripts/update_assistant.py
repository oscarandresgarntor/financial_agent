#!/usr/bin/env python3
"""
Script to update the Andrew assistant on Vapi.

Usage:
    python scripts/update_assistant.py

This script will update Andrew with any changes made to:
- src/agent/prompts.py (system prompt, first message)
- src/agent/andrew.py (voice, LLM, transcriber settings)
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from src.config import config
from src.agent.andrew import ANDREW_CONFIG


VAPI_API_URL = "https://api.vapi.ai"
ASSISTANT_ID = "8a376a7b-b66f-490c-b43a-3af3bb15cd60"


def main():
    """Update the Andrew assistant on Vapi."""
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Updating Andrew on Vapi...")

    try:
        headers = {
            "Authorization": f"Bearer {config.VAPI_API_KEY}",
            "Content-Type": "application/json",
        }

        response = httpx.patch(
            f"{VAPI_API_URL}/assistant/{ASSISTANT_ID}",
            headers=headers,
            json=ANDREW_CONFIG,
            timeout=30.0,
        )

        if response.status_code == 200:
            print("✓ Andrew updated successfully!")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

    except httpx.RequestError as e:
        print(f"✗ Network error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
