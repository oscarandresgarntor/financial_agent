"""
Pydantic models for structured call analysis output.

These models define the structure for capturing conversion success,
customer satisfaction, call duration, and other metrics from voice calls.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConversionStatus(str, Enum):
    """Status indicating whether the customer converted (agreed to apply)."""

    CONVERTED = "converted"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    UNKNOWN = "unknown"


class SatisfactionLevel(str, Enum):
    """Customer satisfaction level based on conversation analysis."""

    VERY_SATISFIED = "very_satisfied"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    DISSATISFIED = "dissatisfied"
    VERY_DISSATISFIED = "very_dissatisfied"


class TranscriptAnalysis(BaseModel):
    """LLM-analyzed metrics from call transcript."""

    conversion_status: ConversionStatus = Field(
        default=ConversionStatus.UNKNOWN,
        description="Whether the customer agreed to apply for the credit card",
    )
    conversion_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for conversion status (0-1)",
    )
    satisfaction_level: SatisfactionLevel = Field(
        default=SatisfactionLevel.NEUTRAL,
        description="Overall customer satisfaction level",
    )
    satisfaction_score: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Satisfaction score on a 1-5 scale",
    )
    satisfaction_reasoning: str = Field(
        default="",
        description="Brief explanation for the satisfaction assessment",
    )
    key_objections: list[str] = Field(
        default_factory=list,
        description="Customer concerns or objections identified in the call",
    )
    positive_signals: list[str] = Field(
        default_factory=list,
        description="Interest indicators and positive engagement signals",
    )
    language_detected: str = Field(
        default="en",
        description="Primary language used in the call (en/es)",
    )


class CallMetrics(BaseModel):
    """Basic call metrics from Vapi webhook."""

    call_id: str = Field(
        description="Unique identifier for the call",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total call duration in seconds",
    )
    cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Call cost in USD",
    )
    ended_reason: Optional[str] = Field(
        default=None,
        description="Reason the call ended (e.g., customer-ended-call, assistant-ended-call)",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the call started",
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the call ended",
    )


class EligibilityOutcome(BaseModel):
    """Credit card eligibility check outcome from the call."""

    was_checked: bool = Field(
        default=False,
        description="Whether eligibility was checked during the call",
    )
    status: Optional[str] = Field(
        default=None,
        description="Eligibility status (eligible, review_required, not_eligible)",
    )
    annual_income: Optional[float] = Field(
        default=None,
        description="Customer's reported annual income",
    )
    has_existing_credit: Optional[bool] = Field(
        default=None,
        description="Whether customer has existing credit history",
    )


class CallAnalysisResult(BaseModel):
    """Complete structured output combining all call analysis data."""

    call_metrics: CallMetrics = Field(
        description="Basic call metrics (duration, cost, timestamps)",
    )
    transcript_analysis: Optional[TranscriptAnalysis] = Field(
        default=None,
        description="LLM-analyzed metrics from transcript",
    )
    eligibility_outcome: EligibilityOutcome = Field(
        default_factory=EligibilityOutcome,
        description="Credit card eligibility check results",
    )
    analysis_error: Optional[str] = Field(
        default=None,
        description="Error message if analysis failed",
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when analysis was performed",
    )
