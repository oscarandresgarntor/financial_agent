"""
Vapi API client for updating call metadata with analysis results.

This service updates completed calls in Vapi with structured analysis
data so it's visible in the Vapi dashboard.
"""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

VAPI_API_BASE = "https://api.vapi.ai"


async def update_call_metadata(
    call_id: str,
    metadata: dict[str, Any],
) -> bool:
    """
    Update a Vapi call record with custom metadata.

    This attaches the analysis results to the call so they're
    visible in the Vapi dashboard under the call's metadata.

    Args:
        call_id: The Vapi call ID to update
        metadata: Dictionary of metadata to attach to the call

    Returns:
        True if update was successful, False otherwise
    """
    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        logger.warning("VAPI_API_KEY not set, cannot update call metadata")
        return False

    if call_id == "unknown" or not call_id:
        logger.warning("Invalid call_id, cannot update metadata")
        return False

    url = f"{VAPI_API_BASE}/call/{call_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Vapi expects metadata under the 'metadata' field
    payload = {
        "metadata": metadata,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                json=payload,
                headers=headers,
                timeout=10.0,
            )

            if response.status_code == 200:
                logger.info(f"Successfully updated call {call_id} with analysis metadata")
                return True
            else:
                logger.error(
                    f"Failed to update call metadata: {response.status_code} - {response.text}"
                )
                return False

    except httpx.TimeoutException:
        logger.error(f"Timeout updating call {call_id} metadata")
        return False
    except Exception as e:
        logger.error(f"Error updating call metadata: {e}")
        return False


def format_analysis_for_vapi(analysis_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Format the analysis result for Vapi metadata storage.

    Flattens and simplifies the structure for better display
    in the Vapi dashboard.

    Args:
        analysis_dict: The CallAnalysisResult as a dictionary

    Returns:
        Formatted metadata dictionary for Vapi
    """
    metadata = {
        "analysis_version": "1.0",
    }

    # Extract call metrics
    call_metrics = analysis_dict.get("call_metrics", {})
    metadata["duration_seconds"] = call_metrics.get("duration_seconds")
    metadata["call_cost"] = call_metrics.get("cost")
    metadata["ended_reason"] = call_metrics.get("ended_reason")

    # Extract transcript analysis (the key insights)
    transcript = analysis_dict.get("transcript_analysis")
    if transcript:
        metadata["conversion_status"] = transcript.get("conversion_status")
        metadata["conversion_confidence"] = transcript.get("conversion_confidence")
        metadata["satisfaction_level"] = transcript.get("satisfaction_level")
        metadata["satisfaction_score"] = transcript.get("satisfaction_score")
        metadata["satisfaction_reasoning"] = transcript.get("satisfaction_reasoning")
        metadata["key_objections"] = transcript.get("key_objections", [])
        metadata["positive_signals"] = transcript.get("positive_signals", [])
        metadata["language_detected"] = transcript.get("language_detected")

    # Extract eligibility outcome
    eligibility = analysis_dict.get("eligibility_outcome", {})
    metadata["eligibility_checked"] = eligibility.get("was_checked", False)
    metadata["eligibility_status"] = eligibility.get("status")
    metadata["customer_income"] = eligibility.get("annual_income")
    metadata["has_existing_credit"] = eligibility.get("has_existing_credit")

    # Add error info if present
    if analysis_dict.get("analysis_error"):
        metadata["analysis_error"] = analysis_dict["analysis_error"]

    metadata["analyzed_at"] = analysis_dict.get("analyzed_at")

    return metadata
