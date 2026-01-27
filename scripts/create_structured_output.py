#!/usr/bin/env python3
"""
Script to create structured outputs for call analysis in Vapi.

This creates a structured output resource that extracts conversion,
satisfaction, and eligibility data from calls, then links it to Andrew.

Usage:
    python scripts/create_structured_output.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from src.config import config

VAPI_API_URL = "https://api.vapi.ai"
ASSISTANT_ID = "8a376a7b-b66f-490c-b43a-3af3bb15cd60"

# Structured output schema for call analysis
CALL_ANALYSIS_OUTPUT = {
    "name": "Bull Bank Call Analysis",
    "type": "ai",
    "description": "Extract conversion status, customer satisfaction, eligibility outcome, and key insights from Bull Bank credit card sales calls.",
    "schema": {
        "type": "object",
        "properties": {
            "conversionStatus": {
                "type": "string",
                "enum": ["converted", "interested", "not_interested", "unknown"],
                "description": "Whether the customer agreed to apply for the credit card. 'converted' = explicitly agreed to apply, 'interested' = showed interest but didn't commit, 'not_interested' = declined, 'unknown' = cannot determine",
            },
            "conversionConfidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence score for the conversion status assessment (0.0 to 1.0)",
            },
            "satisfactionLevel": {
                "type": "string",
                "enum": ["very_satisfied", "satisfied", "neutral", "dissatisfied", "very_dissatisfied"],
                "description": "Overall customer satisfaction based on tone, engagement, and responses during the call",
            },
            "satisfactionScore": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Satisfaction score on a 1-5 scale (1=very dissatisfied, 5=very satisfied)",
            },
            "satisfactionReasoning": {
                "type": "string",
                "description": "Brief 1-2 sentence explanation for the satisfaction assessment",
            },
            "keyObjections": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of specific customer concerns or objections raised (e.g., 'annual fee too high', 'interest rate concerns')",
            },
            "positiveSignals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of interest indicators and positive engagement signals (e.g., 'asked about rewards', 'inquired about credit limit')",
            },
            "eligibilityChecked": {
                "type": "boolean",
                "description": "Whether eligibility was discussed or checked during the call",
            },
            "eligibilityStatus": {
                "type": "string",
                "enum": ["eligible", "review_required", "not_eligible", "not_checked"],
                "description": "Result of eligibility assessment if discussed",
            },
            "customerIncome": {
                "type": "number",
                "description": "Customer's reported annual income if mentioned during the call",
            },
            "hasExistingCredit": {
                "type": "boolean",
                "description": "Whether the customer mentioned having existing credit history",
            },
            "languageUsed": {
                "type": "string",
                "enum": ["english", "spanish", "mixed"],
                "description": "Primary language used in the conversation",
            },
            "callSummary": {
                "type": "string",
                "description": "Brief 2-3 sentence summary of the call outcome, key points discussed, and any follow-up needed",
            },
        },
        "required": [
            "conversionStatus",
            "satisfactionLevel",
            "satisfactionScore",
            "eligibilityChecked",
            "languageUsed",
            "callSummary",
        ],
    },
}


def main():
    """Create structured output and link to Andrew assistant."""
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

    # Step 1: Check for existing structured outputs
    print("Checking for existing structured outputs...")
    response = httpx.get(
        f"{VAPI_API_URL}/structured-output",
        headers=headers,
        timeout=30.0,
    )

    existing_output_id = None
    if response.status_code == 200:
        data = response.json()
        outputs = data.get("results", []) if isinstance(data, dict) else data
        for output in outputs:
            if output.get("name") == CALL_ANALYSIS_OUTPUT["name"]:
                existing_output_id = output["id"]
                print(f"  Found existing output: {existing_output_id}")
                break

    # Step 2: Create or update structured output
    if existing_output_id:
        print(f"Updating existing structured output...")
        response = httpx.patch(
            f"{VAPI_API_URL}/structured-output/{existing_output_id}",
            headers=headers,
            json=CALL_ANALYSIS_OUTPUT,
            timeout=30.0,
        )
        output_id = existing_output_id
    else:
        print("Creating new structured output...")
        response = httpx.post(
            f"{VAPI_API_URL}/structured-output",
            headers=headers,
            json=CALL_ANALYSIS_OUTPUT,
            timeout=30.0,
        )

        if response.status_code not in [200, 201]:
            print(f"✗ Error creating structured output: {response.status_code}")
            print(f"  Response: {response.text}")
            sys.exit(1)

        output_id = response.json().get("id")

    print(f"✓ Structured output ready: {output_id}")

    # Step 3: Link structured output to Andrew assistant
    print(f"\nLinking to assistant {ASSISTANT_ID}...")

    assistant_update = {
        "artifactPlan": {
            "structuredOutputIds": [output_id],
        },
    }

    response = httpx.patch(
        f"{VAPI_API_URL}/assistant/{ASSISTANT_ID}",
        headers=headers,
        json=assistant_update,
        timeout=30.0,
    )

    if response.status_code == 200:
        print("✓ Structured output linked to Andrew!")
        print("\nNext steps:")
        print("  1. Make a test call to Andrew")
        print("  2. After the call ends, go to https://dashboard.vapi.ai/calls")
        print("  3. Click on the call to see 'Structured Outputs' section")
    else:
        print(f"✗ Error linking to assistant: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)

    print(f"\nStructured Output ID: {output_id}")
    print("Save this ID if you need to update the output later.")


if __name__ == "__main__":
    main()
