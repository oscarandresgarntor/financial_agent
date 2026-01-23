"""
FastAPI webhook server for handling Vapi call events.

This server receives webhooks from Vapi for various call events
and processes function calls made by the assistant.
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from ..tools.credit_card import (
    check_credit_card_eligibility,
    format_eligibility_response,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Andrew Voice Agent Webhook Server",
    description="Webhook server for Bull Bank's Voice AI Agent",
    version="0.1.0",
)


class WebhookEvent(BaseModel):
    """Base model for Vapi webhook events."""
    message: dict[str, Any]


class FunctionCallPayload(BaseModel):
    """Payload for function call events."""
    name: str
    parameters: dict[str, Any]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Andrew Voice Agent Webhook Server",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Main webhook endpoint for Vapi events.

    Handles various event types:
    - function-call: Process function calls from the assistant
    - call-start: Log when a call starts
    - call-end: Log when a call ends
    - transcript: Log conversation transcripts
    """
    try:
        payload = await request.json()
        logger.info(f"Received webhook: {json.dumps(payload, indent=2)}")

        message = payload.get("message", {})
        message_type = message.get("type", "")

        # Route to appropriate handler based on message type
        if message_type == "function-call":
            return await handle_function_call(message)

        elif message_type == "status-update":
            status = message.get("status", "")
            logger.info(f"Call status update: {status}")
            return {"status": "received"}

        elif message_type == "end-of-call-report":
            return await handle_call_end(message)

        elif message_type == "transcript":
            return await handle_transcript(message)

        else:
            logger.info(f"Unhandled message type: {message_type}")
            return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_function_call(message: dict) -> dict:
    """
    Process function calls from the assistant.

    Args:
        message: The function call message from Vapi

    Returns:
        The function result to send back to Vapi
    """
    function_call = message.get("functionCall", {})
    function_name = function_call.get("name", "")
    parameters = function_call.get("parameters", {})

    logger.info(f"Function call: {function_name} with params: {parameters}")

    if function_name == "check_credit_card_eligibility":
        # Extract parameters
        annual_income = parameters.get("annual_income", 0)
        has_existing_credit = parameters.get("has_existing_credit")

        # Perform eligibility check
        result = check_credit_card_eligibility(
            annual_income=annual_income,
            has_existing_credit=has_existing_credit,
        )

        # Format response for voice
        voice_response = format_eligibility_response(result)

        return {
            "result": voice_response,
        }

    else:
        logger.warning(f"Unknown function: {function_name}")
        return {
            "result": "I'm sorry, I couldn't process that request. Let me help you another way.",
        }


async def handle_call_end(message: dict) -> dict:
    """
    Handle end-of-call reports.

    Args:
        message: The end-of-call report from Vapi

    Returns:
        Acknowledgment response
    """
    call_id = message.get("call", {}).get("id", "unknown")
    duration = message.get("durationSeconds", 0)
    cost = message.get("cost", 0)

    logger.info(
        f"Call ended - ID: {call_id}, Duration: {duration}s, Cost: ${cost:.4f}"
    )

    # Here you could save call data to a database
    # await save_call_record(call_id, duration, cost, message)

    return {"status": "received"}


async def handle_transcript(message: dict) -> dict:
    """
    Handle transcript events.

    Args:
        message: The transcript message from Vapi

    Returns:
        Acknowledgment response
    """
    transcript = message.get("transcript", "")
    role = message.get("role", "unknown")

    logger.info(f"Transcript [{role}]: {transcript}")

    return {"status": "received"}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the webhook server.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
