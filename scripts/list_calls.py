#!/usr/bin/env python3
"""
Script to list recent calls and their details.

Usage:
    python scripts/list_calls.py
    python scripts/list_calls.py --limit 20
    python scripts/list_calls.py --call-id call_xxx

This script will list recent calls or show details for a specific call.
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from src.config import config


VAPI_API_URL = "https://api.vapi.ai"


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to a readable string."""
    if seconds is None:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def format_cost(cost: float | None) -> str:
    """Format cost to a readable string."""
    if cost is None:
        return "N/A"
    return f"${cost:.4f}"


def main():
    """List recent calls or show call details."""
    parser = argparse.ArgumentParser(
        description="List recent calls and their details"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of calls to list (default: 10)",
    )
    parser.add_argument(
        "--call-id",
        help="Show details for a specific call",
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
        if args.call_id:
            # Show details for specific call
            print(f"Fetching details for call: {args.call_id}\n")

            response = httpx.get(
                f"{VAPI_API_URL}/call/{args.call_id}",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"Error: {response.text}")
                sys.exit(1)

            call = response.json()

            print(f"Call ID: {call['id']}")
            print(f"Status: {call.get('status', 'N/A')}")
            print(f"Type: {call.get('type', 'N/A')}")
            print(f"Duration: {format_duration(call.get('duration'))}")
            print(f"Cost: {format_cost(call.get('cost'))}")

            if call.get('assistant'):
                print(f"Assistant: {call['assistant'].get('name', 'N/A')}")

            if call.get('transcript'):
                print("\n--- Transcript ---")
                print(call['transcript'])
                print("--- End Transcript ---")

        else:
            # List recent calls
            print(f"Listing last {args.limit} calls...\n")

            response = httpx.get(
                f"{VAPI_API_URL}/call",
                headers=headers,
                params={"limit": args.limit},
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"Error: {response.text}")
                sys.exit(1)

            calls = response.json()

            if not calls:
                print("No calls found.")
                return

            print(f"{'ID':<40} {'Status':<12} {'Duration':<10} {'Cost':<10}")
            print("-" * 75)

            for call in calls:
                call_id = call['id'][:35] + "..." if len(call['id']) > 38 else call['id']
                status = call.get('status', 'N/A')
                duration = format_duration(call.get('duration'))
                cost = format_cost(call.get('cost'))

                print(f"{call_id:<40} {status:<12} {duration:<10} {cost:<10}")

            print(f"\nTotal: {len(calls)} calls")
            print("\nUse --call-id <id> to see details for a specific call.")

    except httpx.RequestError as e:
        print(f"\n✗ Network error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
