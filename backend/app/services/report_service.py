from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.assessment import ReportRequest

DISCLAIMER = (
    "CrediLens AI is an educational tool. This report is not an official "
    "credit decision, loan approval, rejection, financial advice, or guarantee."
)

INCOME_FIELDS = tuple(f"income_month_{index}" for index in range(1, 7))


def _currency(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "Not provided"
    return f"INR {value:,.0f}"


def _recommendations(values: dict[str, object]) -> list[str]:
    incomes = [
        float(values[field])
        for field in INCOME_FIELDS
        if isinstance(values.get(field), (int, float))
    ]
    recommendations: list[str] = []
    if len(incomes) >= 2:
        average = sum(incomes) / len(incomes)
        variation = max(incomes) - min(incomes)
        if average > 0 and variation / average > 0.25:
            recommendations.append(
                "Consider maintaining a larger emergency reserve to help manage months with lower reported income."
            )
        else:
            recommendations.append(
                "Continue keeping consistent income records so your financial profile remains easy to review."
            )
    else:
        recommendations.append(
            "Add more monthly income records when available to make future assessments more informative."
        )
    if (
        isinstance(values.get("utility_bills_paid"), (int, float))
        and isinstance(values.get("utility_bills_total"), (int, float))
        and values["utility_bills_total"] > 0
        and values["utility_bills_paid"] < values["utility_bills_total"]
    ):
        recommendations.append(
            "Review outstanding household bills and plan for keeping future payments on schedule."
        )
    if isinstance(values.get("loan_amount_requested"), (int, float)) and values["loan_amount_requested"] > 0:
        recommendations.append(
            "Before taking on additional obligations, compare the requested amount with regular income and existing commitments."
        )
    if len(recommendations) < 3:
        recommendations.append(
            "Keep a record of timely payments and review existing obligations before adding new ones."
        )
    return recommendations[:3]


def generate_report(request: ReportRequest) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="CrediLens assessment report",
        author="CrediLens AI",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0b4b39"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Metric",
            parent=styles["BodyText"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#10231d"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0b4b39"),
            spaceBefore=14,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#60736c"),
        )
    )

    assessment = request.explanation.assessment
    values = request.borrower_input.model_dump()
    generated_at = datetime.now(timezone.utc)
    borrower_type = values.get("borrower_type") or "Not provided"
    incomes = [
        float(values[field])
        for field in INCOME_FIELDS
        if isinstance(values.get(field), (int, float))
    ]
    average_income = sum(incomes) / len(incomes) if incomes else None
    income_range = max(incomes) - min(incomes) if len(incomes) >= 2 else None
    story = [
        Paragraph("CrediLens AI", styles["ReportTitle"]),
        Paragraph("Alternative Credit Assessment Report", styles["Heading2"]),
        Paragraph(
            f"Assessment date: {generated_at.strftime('%Y-%m-%d')} · Reference: CL-{generated_at.strftime('%Y%m%d%H%M%S')}",
            styles["Small"],
        ),
        Spacer(1, 12),
        *(
            [
                Paragraph("Borrower details", styles["Section"]),
                _table(
                    [
                        ["Full name", escape(request.borrower_metadata.full_name)],
                        ["Date of birth", request.borrower_metadata.date_of_birth.isoformat()],
                        ["Borrower type", escape(str(borrower_type))],
                    ]
                ),
            ]
            if request.borrower_metadata is not None
            else []
        ),
        *(
            [
                Paragraph("Additional Financial Context", styles["Section"]),
                _table(
                    [
                        [
                            "Emergency financial resilience",
                            escape(request.financial_context.emergency_financial_resilience)
                            if request.financial_context.emergency_financial_resilience
                            else "Not provided",
                        ],
                        [
                            "Repayment comfort",
                            str(request.financial_context.repayment_comfort)
                            if request.financial_context.repayment_comfort is not None
                            else "Not provided",
                        ],
                    ]
                ),
                Paragraph(
                    "Self-reported context only; these responses are not model-derived and do not independently determine an assessment.",
                    styles["Small"],
                ),
            ]
            if request.financial_context is not None
            else []
        ),
        Paragraph("Executive summary", styles["Section"]),
        _table(
            [
                ["Alternative assessment signal", f"{assessment.risk_probability:.1%} default-risk probability"],
                ["Risk category", assessment.risk_category.capitalize()],
                ["Assessment status", "Validated model response"],
                ["Data completeness", f"{assessment.reliability.level.capitalize()} ({assessment.reliability.score}/100)"],
            ]
        ),
        Paragraph(
            "This result is a model-based assessment signal that should be interpreted alongside the supporting financial details. It is not a standalone lending decision.",
            styles["Small"],
        ),
        Paragraph("Financial overview", styles["Section"]),
        _table(
            [
                ["Average monthly income", _currency(average_income)],
                ["Income months provided", f"{len(incomes)} of 6"],
                ["Income range", _currency(income_range)],
                ["Loan amount requested", _currency(values.get("loan_amount_requested"))],
            ]
        ),
        Paragraph("Income history", styles["Section"]),
        _income_table(values),
        Paragraph("Model explanation", styles["Section"]),
        Paragraph(request.explanation.explanation, styles["BodyText"]),
        Paragraph(
            f"Explanation source: {request.explanation.explanation_source}. "
            f"{request.explanation.disclaimer}",
            styles["Small"],
        ),
        Paragraph("Feature contributions", styles["Section"]),
        _contribution_table(assessment.feature_contributions),
        Paragraph("Reliability details", styles["Section"]),
        Paragraph(assessment.reliability.disclaimer, styles["Small"]),
        _bullet_list(assessment.reliability.reasons, styles),
        Paragraph("Recommended next steps", styles["Section"]),
        _bullet_list(_recommendations(values), styles),
    ]

    if request.simulator is not None:
        simulated = request.simulator.assessment
        story.extend(
            [
                Paragraph("Simulator comparison", styles["Section"]),
                _table(
                    [
                        ["", "Original", "Simulated"],
                        [
                            "Probability",
                            f"{assessment.risk_probability:.1%}",
                            f"{simulated.risk_probability:.1%}",
                        ],
                        ["Category", assessment.risk_category, simulated.risk_category],
                    ]
                ),
                Paragraph(request.simulator.disclaimer, styles["Small"]),
            ]
        )

    story.extend(
        [
            Spacer(1, 18),
            Paragraph(
                DISCLAIMER
                + " Full Name and Date of Birth are report metadata only and are not used as ML prediction features. Self-reported information may require independent verification.",
                styles["Small"],
            ),
        ]
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()


def _table(rows: list[list[str]]) -> Table:
    table = Table(rows, colWidths=[2.0 * inch, 3.9 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f6f2")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8e4de")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#10231d")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _contribution_table(contributions: list) -> Table:
    rows = [["Feature", "Contribution", "Direction"]]
    rows.extend(
        [
            [
                item.feature.replace("_", " "),
                f"{item.contribution:+.4f}",
                item.direction.replace("_", " "),
            ]
            for item in contributions[:10]
        ]
    )
    table = Table(rows, colWidths=[2.3 * inch, 1.2 * inch, 2.4 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b4b39")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8e4de")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ]
        )
    )
    return table


def _income_table(values: dict[str, object]) -> Table:
    rows = [["Period", "Reported income"]]
    rows.extend(
        [
            [f"Month {index}", _currency(values.get(f"income_month_{index}"))]
            for index in range(1, 7)
        ]
    )
    table = Table(rows, colWidths=[2.0 * inch, 3.9 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b4b39")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8e4de")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ]
        )
    )
    return table


def _input_table(values: dict) -> Table:
    rows = [["Input", "Value"]]
    rows.extend(
        [
            [str(name).replace("_", " "), "Not provided" if value is None else str(value)]
            for name, value in values.items()
        ]
    )
    table = Table(rows, colWidths=[3.2 * inch, 2.7 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b4b39")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d8e4de")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _bullet_list(items: list[str], styles) -> KeepTogether:
    return KeepTogether(
        [Paragraph(f"• {item}", styles["Small"]) for item in items]
    )


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#60736c"))
    canvas.drawString(document.leftMargin, 0.35 * inch, DISCLAIMER)
    canvas.drawRightString(7.85 * inch, 0.35 * inch, f"Page {document.page}")
    canvas.restoreState()
