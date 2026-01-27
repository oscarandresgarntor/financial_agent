"""
Transcript analysis service using LLM for extracting call metrics.

Uses OpenAI GPT-4o to analyze call transcripts and extract
conversion status, satisfaction levels, objections, and other insights.
"""

import json
import logging
import os
from typing import Optional

from openai import OpenAI

from ..models.call_analysis import (
    ConversionStatus,
    SatisfactionLevel,
    TranscriptAnalysis,
)

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze this customer service call transcript from a bank credit card offer call.

Extract the following information:

1. **Conversion Status**: Did the customer agree to apply for the credit card?
   - "converted": Customer explicitly agreed to apply or proceed
   - "interested": Customer showed interest but didn't commit
   - "not_interested": Customer declined or showed no interest
   - "unknown": Cannot determine from transcript

2. **Conversion Confidence**: How confident are you in this assessment? (0.0 to 1.0)

3. **Satisfaction Level**: How satisfied did the customer seem?
   - "very_satisfied": Expressed gratitude, enthusiasm
   - "satisfied": Positive, engaged
   - "neutral": Neither positive nor negative
   - "dissatisfied": Expressed frustration or concerns
   - "very_dissatisfied": Angry, complained, or was hostile

4. **Satisfaction Score**: Rate satisfaction 1-5 (1=very dissatisfied, 5=very satisfied)

5. **Satisfaction Reasoning**: Brief explanation (1-2 sentences) for satisfaction assessment

6. **Key Objections**: List specific concerns the customer raised (e.g., "annual fee too high", "interest rate concerns")

7. **Positive Signals**: List indicators of interest (e.g., "asked about rewards program", "inquired about credit limit")

8. **Language Detected**: Primary language used ("en" for English, "es" for Spanish)

Respond with ONLY valid JSON in this exact format:
{
    "conversion_status": "converted|interested|not_interested|unknown",
    "conversion_confidence": 0.0,
    "satisfaction_level": "very_satisfied|satisfied|neutral|dissatisfied|very_dissatisfied",
    "satisfaction_score": 3,
    "satisfaction_reasoning": "Brief explanation here",
    "key_objections": ["objection 1", "objection 2"],
    "positive_signals": ["signal 1", "signal 2"],
    "language_detected": "en"
}

TRANSCRIPT:
"""


def analyze_transcript(transcript: str) -> Optional[TranscriptAnalysis]:
    """
    Analyze a call transcript using OpenAI GPT-4o.

    Args:
        transcript: The full call transcript text

    Returns:
        TranscriptAnalysis model with extracted metrics, or None if analysis fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping transcript analysis")
        return None

    if not transcript or len(transcript.strip()) < 50:
        logger.warning("Transcript too short for meaningful analysis")
        return None

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing customer service call transcripts. Always respond with valid JSON only.",
                },
                {
                    "role": "user",
                    "content": ANALYSIS_PROMPT + transcript,
                },
            ],
            temperature=0.3,
            max_tokens=500,
        )

        result_text = response.choices[0].message.content
        if not result_text:
            logger.error("Empty response from OpenAI")
            return create_fallback_analysis()

        # Clean up response (remove markdown code blocks if present)
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit("```", 1)[0]
        result_text = result_text.strip()

        # Parse JSON response
        analysis_data = json.loads(result_text)

        # Map string values to enums
        conversion_status = ConversionStatus(analysis_data.get("conversion_status", "unknown"))
        satisfaction_level = SatisfactionLevel(analysis_data.get("satisfaction_level", "neutral"))

        return TranscriptAnalysis(
            conversion_status=conversion_status,
            conversion_confidence=float(analysis_data.get("conversion_confidence", 0.0)),
            satisfaction_level=satisfaction_level,
            satisfaction_score=int(analysis_data.get("satisfaction_score", 3)),
            satisfaction_reasoning=analysis_data.get("satisfaction_reasoning", ""),
            key_objections=analysis_data.get("key_objections", []),
            positive_signals=analysis_data.get("positive_signals", []),
            language_detected=analysis_data.get("language_detected", "en"),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return create_fallback_analysis()
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}")
        return create_fallback_analysis()


def create_fallback_analysis() -> TranscriptAnalysis:
    """
    Create a fallback analysis with neutral/unknown values.

    Used when LLM analysis fails to ensure we always return structured data.

    Returns:
        TranscriptAnalysis with default neutral values
    """
    return TranscriptAnalysis(
        conversion_status=ConversionStatus.UNKNOWN,
        conversion_confidence=0.0,
        satisfaction_level=SatisfactionLevel.NEUTRAL,
        satisfaction_score=3,
        satisfaction_reasoning="Analysis could not be performed",
        key_objections=[],
        positive_signals=[],
        language_detected="en",
    )
