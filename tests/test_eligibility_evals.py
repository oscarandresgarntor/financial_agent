"""
Eval tests for credit card eligibility logic.

Two groups of evals:
  A) Deterministic evals — pure assert-based checks on business logic (no LLM cost)
  B) LLM-as-judge evals — Gemini evaluates the quality of voice responses

Run all:       deepeval test run tests/test_eligibility_evals.py
Run fast only: deepeval test run tests/test_eligibility_evals.py -k "deterministic"
"""

import os
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCaseParams

from src.tools.credit_card import (
    check_credit_card_eligibility,
    format_eligibility_response,
    EligibilityStatus,
)

# ---------------------------------------------------------------------------
# Group A: Deterministic evals — business logic correctness (no LLM needed)
# ---------------------------------------------------------------------------


class TestDeterministicEligibility:
    """Assert-based checks that the eligibility function returns the correct status."""

    def test_deterministic_high_income_eligible(self):
        """Income >= $25,000 → ELIGIBLE."""
        result = check_credit_card_eligibility(annual_income=50000)
        assert result.status == EligibilityStatus.ELIGIBLE

    def test_deterministic_exact_threshold_eligible(self):
        """Exactly $25,000 → ELIGIBLE (boundary)."""
        result = check_credit_card_eligibility(annual_income=25000)
        assert result.status == EligibilityStatus.ELIGIBLE

    def test_deterministic_below_threshold_with_credit_review(self):
        """Income < $25,000 + has credit → REVIEW_REQUIRED."""
        result = check_credit_card_eligibility(
            annual_income=20000, has_existing_credit=True
        )
        assert result.status == EligibilityStatus.REVIEW_REQUIRED

    def test_deterministic_below_threshold_no_credit_not_eligible(self):
        """Income < $25,000 + no credit → NOT_ELIGIBLE."""
        result = check_credit_card_eligibility(
            annual_income=15000, has_existing_credit=False
        )
        assert result.status == EligibilityStatus.NOT_ELIGIBLE

    def test_deterministic_zero_income_no_credit_not_eligible(self):
        """Zero income + no credit → NOT_ELIGIBLE."""
        result = check_credit_card_eligibility(
            annual_income=0, has_existing_credit=False
        )
        assert result.status == EligibilityStatus.NOT_ELIGIBLE

    def test_deterministic_below_threshold_credit_none_not_eligible(self):
        """Income < $25,000 + credit=None (unknown) → NOT_ELIGIBLE."""
        result = check_credit_card_eligibility(
            annual_income=15000, has_existing_credit=None
        )
        assert result.status == EligibilityStatus.NOT_ELIGIBLE

    def test_deterministic_result_fields_populated(self):
        """All result fields should be populated."""
        result = check_credit_card_eligibility(annual_income=30000)
        assert result.message != ""
        assert result.recommended_action != ""
        assert result.annual_income == 30000

    def test_deterministic_format_response_combines_message_and_action(self):
        """format_eligibility_response joins message and recommended_action."""
        result = check_credit_card_eligibility(annual_income=50000)
        response = format_eligibility_response(result)
        assert result.message in response
        assert result.recommended_action in response


# ---------------------------------------------------------------------------
# Group B: LLM-as-judge evals — evaluate voice response quality with Gemini
# ---------------------------------------------------------------------------

# The LLM judge model — free via Google AI Studio
# DeepEval's GeminiModel reads from GOOGLE_API_KEY env var
JUDGE_MODEL = GeminiModel(model="gemini-2.0-flash")

# Skip LLM-as-judge tests if no Google API key is set
requires_llm = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — skipping LLM-as-judge evals",
)


def _build_test_case(annual_income: float, has_existing_credit: bool | None = None) -> LLMTestCase:
    """Helper: run eligibility check and build an LLMTestCase from the response."""
    result = check_credit_card_eligibility(annual_income, has_existing_credit)
    response = format_eligibility_response(result)

    # For LLM-as-judge, 'input' is what the customer asked and
    # 'actual_output' is the agent's voice response.
    return LLMTestCase(
        input=f"Check eligibility: income=${annual_income}, has_credit={has_existing_credit}",
        actual_output=response,
    )


# --- Metric definitions ---

def _professionalism_metric() -> GEval:
    return GEval(
        name="Professionalism",
        criteria=(
            "The response should be empathetic, professional, and appropriate "
            "for a bank customer service voice call. It should not be rude, "
            "dismissive, or overly casual."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        model=JUDGE_MODEL,
        threshold=0.7,
    )


def _correctness_metric(expected_status: str) -> GEval:
    return GEval(
        name="Status Correctness",
        criteria=(
            f"The response must accurately reflect that the customer's eligibility "
            f"status is '{expected_status}'. It must NOT claim the customer is "
            f"eligible when they are not, or vice versa."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        model=JUDGE_MODEL,
        threshold=0.7,
    )


def _actionability_metric() -> GEval:
    return GEval(
        name="Clear Next Step",
        criteria=(
            "The response must include a clear, actionable next step for the "
            "customer — for example, proceeding with an application, waiting for "
            "review, or considering an alternative product."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        model=JUDGE_MODEL,
        threshold=0.7,
    )


def _voice_appropriate_metric() -> GEval:
    return GEval(
        name="Voice Appropriate",
        criteria=(
            "The response should be suitable for a voice conversation: concise "
            "(under 3 sentences), no markdown formatting, no special characters, "
            "no bullet points, and easy to understand when spoken aloud."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        model=JUDGE_MODEL,
        threshold=0.7,
    )


# --- LLM-as-judge test cases ---

@requires_llm
class TestLLMJudgeEligibleResponse:
    """LLM-as-judge evals for the ELIGIBLE scenario."""

    def test_llm_judge_eligible_professional(self):
        test_case = _build_test_case(annual_income=50000)
        assert_test(test_case, [_professionalism_metric()])

    def test_llm_judge_eligible_correct_status(self):
        test_case = _build_test_case(annual_income=50000)
        assert_test(test_case, [_correctness_metric("eligible")])

    def test_llm_judge_eligible_actionable(self):
        test_case = _build_test_case(annual_income=50000)
        assert_test(test_case, [_actionability_metric()])

    def test_llm_judge_eligible_voice_appropriate(self):
        test_case = _build_test_case(annual_income=50000)
        assert_test(test_case, [_voice_appropriate_metric()])


@requires_llm
class TestLLMJudgeReviewResponse:
    """LLM-as-judge evals for the REVIEW_REQUIRED scenario."""

    def test_llm_judge_review_professional(self):
        test_case = _build_test_case(annual_income=20000, has_existing_credit=True)
        assert_test(test_case, [_professionalism_metric()])

    def test_llm_judge_review_correct_status(self):
        test_case = _build_test_case(annual_income=20000, has_existing_credit=True)
        assert_test(test_case, [_correctness_metric("review_required")])

    def test_llm_judge_review_actionable(self):
        test_case = _build_test_case(annual_income=20000, has_existing_credit=True)
        assert_test(test_case, [_actionability_metric()])

    def test_llm_judge_review_voice_appropriate(self):
        test_case = _build_test_case(annual_income=20000, has_existing_credit=True)
        assert_test(test_case, [_voice_appropriate_metric()])


@requires_llm
class TestLLMJudgeNotEligibleResponse:
    """LLM-as-judge evals for the NOT_ELIGIBLE scenario."""

    def test_llm_judge_not_eligible_professional(self):
        test_case = _build_test_case(annual_income=15000, has_existing_credit=False)
        assert_test(test_case, [_professionalism_metric()])

    def test_llm_judge_not_eligible_correct_status(self):
        test_case = _build_test_case(annual_income=15000, has_existing_credit=False)
        assert_test(test_case, [_correctness_metric("not_eligible")])

    def test_llm_judge_not_eligible_actionable(self):
        test_case = _build_test_case(annual_income=15000, has_existing_credit=False)
        assert_test(test_case, [_actionability_metric()])

    def test_llm_judge_not_eligible_voice_appropriate(self):
        test_case = _build_test_case(annual_income=15000, has_existing_credit=False)
        assert_test(test_case, [_voice_appropriate_metric()])
