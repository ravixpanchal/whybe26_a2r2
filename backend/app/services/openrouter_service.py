from __future__ import annotations

import time
import re
from typing import Any

import httpx

from app.config import Settings
from app.schemas.assessment import AssessmentResponse

EXPLANATION_DISCLAIMER = (
    "This explanation translates the validated model output for education. "
    "It is not a loan decision, approval, rejection, or financial advice."
)
_FORBIDDEN_PHRASES = (
    "you are approved",
    "you are rejected",
    "loan is approved",
    "loan is rejected",
    "should approve",
    "should reject",
    "guarantee",
    "guaranteed",
    "confidence interval",
    "you will default",
)


class OpenRouterService:
    def __init__(
        self,
        settings: Settings,
        client: Any | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        self._settings = settings
        self._client = client
        self._sleep = sleep

    def explain(self, assessment: AssessmentResponse) -> tuple[str, str]:
        fallback = self._fallback(assessment)
        if not self._settings.openrouter_api_key:
            return fallback, "fallback"

        payload = self._payload(assessment)
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        for attempt in range(2):
            try:
                response = self._post(payload, headers)
                if response.status_code in {408, 429} or response.status_code >= 500:
                    if attempt == 0:
                        self._sleep(0.1)
                        continue
                    return fallback, "fallback"
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not self._is_safe(
                    content, assessment.risk_category
                ):
                    return fallback, "fallback"
                return content.strip(), "openrouter"
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
                if attempt == 0:
                    self._sleep(0.1)
                    continue
                return fallback, "fallback"
        return fallback, "fallback"

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> Any:
        if self._client is not None:
            return self._client.post(
                "/chat/completions",
                headers=headers,
                json=payload,
                timeout=self._settings.openrouter_timeout_seconds,
            )
        with httpx.Client(
            base_url=self._settings.openrouter_base_url,
            timeout=self._settings.openrouter_timeout_seconds,
        ) as client:
            return client.post("/chat/completions", headers=headers, json=payload)

    def _payload(self, assessment: AssessmentResponse) -> dict[str, Any]:
        factors = [
            {
                "feature": factor.feature,
                "direction": factor.direction,
                "contribution": factor.contribution,
            }
            for factor in assessment.feature_contributions[:5]
        ]
        structured = {
            "risk_category": assessment.risk_category,
            "risk_probability": assessment.risk_probability,
            "top_feature_contributions": factors,
            "reliability_level": assessment.reliability.level,
            "reliability_reasons": assessment.reliability.reasons,
        }
        return {
            "model": self._settings.openrouter_model,
            "temperature": 0,
            "max_tokens": 180,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You translate a fixed machine-learning result into plain "
                        "educational language. Never recalculate or change the "
                        "result. Do not make a lending decision, invent borrower "
                        "facts, or claim certainty. Mention that this is not a "
                        "loan approval or rejection."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Explain this structured result in 2-4 concise sentences. "
                        "Use only these values:\n" + str(structured)
                    ),
                },
            ],
        }

    @staticmethod
    def _is_safe(content: str, category: str) -> bool:
        lowered = content.lower()
        if len(content) > 2000 or any(term in lowered for term in _FORBIDDEN_PHRASES):
            return False
        if "approved" in lowered and "not a loan approval" not in lowered:
            return False
        categories = {"low", "moderate", "high"}
        if not re.search(rf"\b{re.escape(category.lower())}\b", lowered):
            return False
        if any(
            other != category.lower()
            and re.search(rf"\b{re.escape(other)}\b", lowered)
            for other in categories
        ):
            return False
        return True

    @staticmethod
    def _fallback(assessment: AssessmentResponse) -> str:
        factors = assessment.feature_contributions[:2]
        factor_text = ", ".join(factor.feature for factor in factors) or "the submitted features"
        return (
            f"The validated model places this assessment in the "
            f"{assessment.risk_category} risk category with a "
            f"{assessment.risk_probability:.1%} default-risk probability. "
            f"The most influential factors in this result include {factor_text}. "
            "This is an educational model explanation, not a loan approval or rejection."
        )
