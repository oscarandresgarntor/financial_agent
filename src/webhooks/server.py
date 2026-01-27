"""
FastAPI webhook server for handling Vapi call events.

This server receives webhooks from Vapi for various call events
and processes function calls made by the assistant.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from ..models.call_analysis import (
    CallAnalysisResult,
    CallMetrics,
    EligibilityOutcome,
)
from ..services.transcript_analyzer import analyze_transcript
from ..services.vapi_client import format_analysis_for_vapi, update_call_metadata
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
    Handle end-of-call reports with structured analysis.

    Extracts call metrics, analyzes the transcript using LLM,
    and returns comprehensive call analysis data.

    Args:
        message: The end-of-call report from Vapi

    Returns:
        Structured call analysis result
    """
    # Extract call metrics
    call_data = message.get("call", {})
    call_id = call_data.get("id", "unknown")
    duration = message.get("durationSeconds", 0)
    cost = message.get("cost", 0)
    ended_reason = message.get("endedReason")

    # Parse timestamps
    started_at = _parse_timestamp(call_data.get("startedAt"))
    ended_at = _parse_timestamp(call_data.get("endedAt"))

    call_metrics = CallMetrics(
        call_id=call_id,
        duration_seconds=float(duration),
        cost=float(cost),
        ended_reason=ended_reason,
        started_at=started_at,
        ended_at=ended_at,
    )

    logger.info(
        f"Call ended - ID: {call_id}, Duration: {duration}s, Cost: ${cost:.4f}"
    )

    # Extract transcript for analysis
    transcript = _extract_transcript(message)

    # Extract eligibility outcome from function calls
    eligibility_outcome = _extract_eligibility_outcome(message)

    # Perform LLM analysis on transcript
    analysis_error = None
    transcript_analysis = None

    if transcript and len(transcript) >= 50:
        try:
            transcript_analysis = analyze_transcript(transcript)
            if transcript_analysis is None:
                analysis_error = "Transcript analysis returned no results (API key may be missing)"
        except Exception as e:
            logger.error(f"Error during transcript analysis: {e}")
            analysis_error = f"Analysis failed: {str(e)}"
    else:
        analysis_error = "Transcript too short or empty for analysis"

    # Build complete analysis result
    analysis_result = CallAnalysisResult(
        call_metrics=call_metrics,
        transcript_analysis=transcript_analysis,
        eligibility_outcome=eligibility_outcome,
        analysis_error=analysis_error,
        analyzed_at=datetime.utcnow(),
    )

    # Log the structured output
    analysis_dict = analysis_result.model_dump(mode="json")
    logger.info(f"Call Analysis Result: {json.dumps(analysis_dict, indent=2)}")

    # Update Vapi call metadata so analysis is visible in dashboard
    vapi_metadata = format_analysis_for_vapi(analysis_dict)
    update_success = await update_call_metadata(call_id, vapi_metadata)

    if update_success:
        logger.info(f"Analysis metadata pushed to Vapi for call {call_id}")
    else:
        logger.warning(f"Failed to push analysis metadata to Vapi for call {call_id}")

    return {
        "status": "received",
        "analysis": analysis_dict,
        "vapi_metadata_updated": update_success,
    }


def _parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime object."""
    if not timestamp_str:
        return None
    try:
        # Handle various ISO formats
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return None


def _extract_transcript(message: dict) -> str:
    """
    Extract full transcript from end-of-call report.

    Args:
        message: The end-of-call report from Vapi

    Returns:
        Combined transcript text
    """
    transcript_parts = []

    # Try to get transcript from artifact
    artifact = message.get("artifact", {})
    messages = artifact.get("messages", [])

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("message", "") or msg.get("content", "")
        if content:
            transcript_parts.append(f"{role}: {content}")

    # Fallback: try direct transcript field
    if not transcript_parts:
        direct_transcript = message.get("transcript", "")
        if direct_transcript:
            return direct_transcript

    return "\n".join(transcript_parts)


def _extract_eligibility_outcome(message: dict) -> EligibilityOutcome:
    """
    Extract eligibility check outcome from function call results.

    Args:
        message: The end-of-call report from Vapi

    Returns:
        EligibilityOutcome with extracted data
    """
    outcome = EligibilityOutcome(was_checked=False)

    # Look through artifact messages for function calls
    artifact = message.get("artifact", {})
    messages = artifact.get("messages", [])

    for msg in messages:
        # Check for tool calls (function calls)
        tool_calls = msg.get("toolCalls", [])
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            if function.get("name") == "check_credit_card_eligibility":
                outcome.was_checked = True

                # Extract parameters
                try:
                    arguments = function.get("arguments", "{}")
                    if isinstance(arguments, str):
                        params = json.loads(arguments)
                    else:
                        params = arguments

                    outcome.annual_income = params.get("annual_income")
                    outcome.has_existing_credit = params.get("has_existing_credit")
                except (json.JSONDecodeError, TypeError):
                    pass

        # Check for tool call results
        tool_call_result = msg.get("toolCallResult", {})
        if tool_call_result.get("name") == "check_credit_card_eligibility":
            outcome.was_checked = True
            result = tool_call_result.get("result", "")

            # Try to extract status from result
            if "eligible" in result.lower():
                if "not eligible" in result.lower():
                    outcome.status = "not_eligible"
                elif "review" in result.lower():
                    outcome.status = "review_required"
                else:
                    outcome.status = "eligible"

    return outcome


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
