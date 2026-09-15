from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BorrowerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    borrower_type: str | None = Field(default=None, min_length=1)
    household_size: int | None = Field(default=None, ge=0)
    income_month_1: float | None = Field(default=None, ge=0)
    income_month_2: float | None = Field(default=None, ge=0)
    income_month_3: float | None = Field(default=None, ge=0)
    income_month_4: float | None = Field(default=None, ge=0)
    income_month_5: float | None = Field(default=None, ge=0)
    income_month_6: float | None = Field(default=None, ge=0)
    employment_type: str | None = Field(default=None, min_length=1)
    months_at_current_job: int | None = Field(default=None, ge=0)
    num_income_sources: int | None = Field(default=None, ge=0)
    upi_transactions_per_month: float | None = Field(default=None, ge=0)
    upi_avg_transaction_amount: float | None = Field(default=None, ge=0)
    upi_months_active: float | None = Field(default=None, ge=0)
    mobile_wallet_used: int | None = Field(default=None, ge=0, le=1)
    utility_bills_paid: int | None = Field(default=None, ge=0)
    utility_bills_total: int | None = Field(default=None, ge=0)
    rent_paid_on_time_months: float | None = Field(default=None, ge=0)
    total_rental_months: float | None = Field(default=None, ge=0)
    same_number_since_year: int | None = Field(default=None, ge=1900, le=2100)
    avg_monthly_recharge_amount: float | None = Field(default=None, ge=0)
    recharge_frequency_per_month: float | None = Field(default=None, ge=0)
    ecomm_orders_per_month: float | None = Field(default=None, ge=0)
    ecomm_return_rate: float | None = Field(default=None, ge=0, le=1)
    prepaid_orders_ratio: float | None = Field(default=None, ge=0, le=1)
    survey_q1: int | None = Field(default=None, ge=1, le=5)
    survey_q2: int | None = Field(default=None, ge=1, le=5)
    survey_q3: int | None = Field(default=None, ge=1, le=5)
    survey_q4: int | None = Field(default=None, ge=1, le=5)
    survey_q5: int | None = Field(default=None, ge=1, le=5)
    survey_q6: int | None = Field(default=None, ge=1, le=5)
    survey_q7: int | None = Field(default=None, ge=1, le=5)
    survey_q8: int | None = Field(default=None, ge=1, le=5)
    loan_amount_requested: float | None = Field(default=None, ge=0)
    loan_purpose: str | None = Field(default=None, min_length=1)
    loan_tenure_months: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_consistency(self) -> "BorrowerInput":
        missing = set(type(self).model_fields) - self.model_fields_set
        if missing:
            raise ValueError(f"Missing required borrower features: {sorted(missing)}")
        if (
            self.utility_bills_paid is not None
            and self.utility_bills_total is not None
            and self.utility_bills_paid > self.utility_bills_total
        ):
            raise ValueError("utility_bills_paid cannot exceed utility_bills_total")
        if (
            self.rent_paid_on_time_months is not None
            and self.total_rental_months is not None
            and self.rent_paid_on_time_months > self.total_rental_months
        ):
            raise ValueError("rent_paid_on_time_months cannot exceed total_rental_months")
        if (
            self.num_income_sources is not None
            and self.num_income_sources == 0
            and any(
                value is not None and value > 0
                for value in (
                    self.income_month_1,
                    self.income_month_2,
                    self.income_month_3,
                    self.income_month_4,
                    self.income_month_5,
                    self.income_month_6,
                )
            )
        ):
            raise ValueError("positive income requires at least one income source")
        return self


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    borrower_input: BorrowerInput


class ModelPrediction(BaseModel):
    model_name: Literal["soft_voting_ensemble"]
    predicted_class: str
    probability: float = Field(ge=0, le=1)


class ModelComparison(BaseModel):
    prediction: ModelPrediction
    primary_model: Literal["soft_voting_ensemble"]
    compatibility_status: Literal["validated"]


class FeatureContribution(BaseModel):
    feature: str
    contribution: float
    direction: Literal["risk_increasing", "risk_reducing"]


class ReliabilityInfo(BaseModel):
    level: Literal["high", "medium", "low"]
    score: int = Field(ge=0, le=100)
    reasons: list[str]
    disclaimer: str


class AssessmentResponse(BaseModel):
    model_comparison: ModelComparison
    risk_probability: float = Field(ge=0, le=1)
    risk_category: Literal["low", "moderate", "high"]
    class_mapping: dict[str, Any]
    feature_contributions: list[FeatureContribution]
    reliability: ReliabilityInfo


class ExplanationResponse(BaseModel):
    assessment: AssessmentResponse
    explanation: str
    explanation_source: Literal["openrouter", "fallback"]
    disclaimer: str
