"""
Andrew assistant configuration for Vapi.ai

This module contains the complete configuration for creating
the Andrew voice assistant on the Vapi platform.
"""

import os

from .prompts import ANDREW_SYSTEM_PROMPT, ANDREW_FIRST_MESSAGE


# Get webhook URL from environment (e.g., ngrok URL or production server)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Structured Output ID (created via scripts/create_structured_output.py)
STRUCTURED_OUTPUT_ID = os.getenv(
    "STRUCTURED_OUTPUT_ID",
    "3626407e-979e-49ef-b93e-4e8105d4312b"
)


# Voice configuration using ElevenLabs
VOICE_CONFIG = {
    "provider": "11labs",
    "voiceId": "pNInz6obpgDQGcFmaJgB",  # "Adam" - professional male voice
    "stability": 0.5,
    "similarityBoost": 0.75,
    "model": "eleven_multilingual_v2",  # Better pronunciation for Spanish
}

# LLM configuration using OpenAI GPT-4o
LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "maxTokens": 500,
    "messages": [
        {
            "role": "system",
            "content": ANDREW_SYSTEM_PROMPT,
        }
    ],
}

# Complete Andrew assistant configuration
ANDREW_CONFIG = {
    "name": "Andrew - Bull Bank Representative",
    "voice": VOICE_CONFIG,
    "model": LLM_CONFIG,
    "firstMessage": ANDREW_FIRST_MESSAGE,
    "firstMessageMode": "assistant-speaks-first",
    # Transcription settings (multi-language support)
    "transcriber": {
        "provider": "deepgram",
        "model": "nova-2",
        "language": "multi",  # Auto-detect English and Spanish
    },
    # Call behavior settings
    "silenceTimeoutSeconds": 30,
    "maxDurationSeconds": 600,  # 10 minute max call
    "endCallMessage": "Thank you for calling Bull Bank. Have a great day!",
    "endCallPhrases": ["goodbye", "bye", "that's all", "I'm done"],
    # Structured outputs for call analysis (linked via artifactPlan)
    # Created separately with scripts/create_structured_output.py
    "artifactPlan": {
        "structuredOutputIds": [STRUCTURED_OUTPUT_ID],
    },
    # Metadata
    "metadata": {
        "agent_type": "credit_card_sales",
        "bank": "Bull Bank",
        "product": "Bank-travel Credit Card",
    },
}

# Add webhook server URL if configured
# This tells Vapi where to send all webhook events including end-of-call-report
if WEBHOOK_URL:
    ANDREW_CONFIG["serverUrl"] = f"{WEBHOOK_URL}/webhook"
    ANDREW_CONFIG["serverMessages"] = [
        "end-of-call-report",  # Triggers structured call analysis
        "status-update",       # Call status changes
        "transcript",          # Real-time transcript updates
    ]


def create_andrew_assistant(vapi_client) -> dict:
    """
    Create the Andrew assistant on Vapi.

    Args:
        vapi_client: Initialized Vapi client instance

    Returns:
        dict: The created assistant object from Vapi
    """
    assistant = vapi_client.assistants.create(**ANDREW_CONFIG)
    return assistant


def update_andrew_assistant(vapi_client, assistant_id: str) -> dict:
    """
    Update an existing Andrew assistant on Vapi.

    Args:
        vapi_client: Initialized Vapi client instance
        assistant_id: The ID of the assistant to update

    Returns:
        dict: The updated assistant object from Vapi
    """
    assistant = vapi_client.assistants.update(
        id=assistant_id,
        **ANDREW_CONFIG
    )
    return assistant
