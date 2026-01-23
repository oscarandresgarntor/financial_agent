#!/usr/bin/env python3
"""
Script to create the Andrew assistant on Vapi.

Usage:
    python scripts/create_assistant.py

This script will:
1. Load configuration from .env
2. Create the Andrew assistant on Vapi
3. Output the assistant ID for future reference
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from src.config import config
from src.agent.andrew import ANDREW_CONFIG


VAPI_API_URL = "https://api.vapi.ai"


def main():
    """Create the Andrew assistant on Vapi."""
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease set the required environment variables in .env")
        sys.exit(1)

    print("Creating Andrew assistant on Vapi...")
    print(f"  Name: {ANDREW_CONFIG['name']}")
    print(f"  Voice: {ANDREW_CONFIG['voice']['provider']}")
    print(f"  LLM: {ANDREW_CONFIG['model']['provider']} / {ANDREW_CONFIG['model']['model']}")

    try:
        # Create the assistant using Vapi REST API
        headers = {
            "Authorization": f"Bearer {config.VAPI_API_KEY}",
            "Content-Type": "application/json",
        }

        response = httpx.post(
            f"{VAPI_API_URL}/assistant",
            headers=headers,
            json=ANDREW_CONFIG,
            timeout=30.0,
        )

        if response.status_code != 201:
            print(f"\n✗ Error creating assistant: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        assistant = response.json()

        print("\n✓ Assistant created successfully!")
        print(f"\n  Assistant ID: {assistant['id']}")
        print(f"  Name: {assistant['name']}")
        print("\nNext steps:")
        print("  1. Go to https://dashboard.vapi.ai/assistants")
        print("  2. Find your assistant and click 'Test Call' to try it")
        print("  3. Get a phone number from Vapi and assign it to this assistant")
        print(f"\nSave this Assistant ID for future reference: {assistant['id']}")

        return assistant['id']

    except httpx.RequestError as e:
        print(f"\n✗ Network error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error creating assistant: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
