#!/usr/bin/env python3
"""
Script to trigger a test outbound call with Andrew.

Usage:
    python scripts/test_call.py --phone +1234567890
    python scripts/test_call.py --assistant-id asst_xxx --phone +1234567890

This script will initiate an outbound call to the specified phone number
using the Andrew assistant.
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from src.config import config


VAPI_API_URL = "https://api.vapi.ai"


def main():
    """Trigger a test call with Andrew."""
    parser = argparse.ArgumentParser(
        description="Trigger a test outbound call with Andrew"
    )
    parser.add_argument(
        "--phone",
        required=True,
        help="Phone number to call (E.164 format, e.g., +1234567890)",
    )
    parser.add_argument(
        "--assistant-id",
        help="Assistant ID to use (optional, will list assistants if not provided)",
    )
    args = parser.parse_args()

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {config.VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        # If no assistant ID provided, list available assistants
        assistant_id = args.assistant_id
        if not assistant_id:
            print("No assistant ID provided. Listing available assistants...\n")

            response = httpx.get(
                f"{VAPI_API_URL}/assistant",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"Error fetching assistants: {response.text}")
                sys.exit(1)

            assistants = response.json()

            if not assistants:
                print("No assistants found. Run create_assistant.py first.")
                sys.exit(1)

            for i, assistant in enumerate(assistants, 1):
                print(f"  {i}. {assistant['name']} (ID: {assistant['id']})")

            print("\nRe-run with --assistant-id to specify which assistant to use.")
            sys.exit(0)

        # Create outbound call
        print(f"Initiating call to {args.phone}...")
        print(f"Using assistant: {assistant_id}")

        response = httpx.post(
            f"{VAPI_API_URL}/call/phone",
            headers=headers,
            json={
                "assistantId": assistant_id,
                "customer": {
                    "number": args.phone,
                },
            },
            timeout=30.0,
        )

        if response.status_code != 201:
            print(f"\n✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        call = response.json()

        print(f"\n✓ Call initiated successfully!")
        print(f"  Call ID: {call['id']}")
        print(f"  Status: {call.get('status', 'initiated')}")
        print("\nThe call should be connecting now. Check your phone!")

    except httpx.RequestError as e:
        print(f"\n✗ Network error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
