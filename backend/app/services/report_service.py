from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

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
    story = [
        Paragraph("CrediLens AI", styles["ReportTitle"]),
        Paragraph("Educational borrower assessment report", styles["Normal"]),
        Paragraph(
            datetime.now(timezone.utc).strftime("Generated %Y-%m-%d %H:%M UTC"),
            styles["Small"],
        ),
        Spacer(1, 12),
        Paragraph("Summary", styles["Section"]),
        _table(
            [
                ["Risk probability", f"{assessment.risk_probability:.1%}"],
                ["Risk category", assessment.risk_category.capitalize()],
                ["Primary model", "Validated soft-voting ensemble"],
                ["Predicted class", assessment.model_comparison.prediction.predicted_class],
                ["Compatibility", assessment.model_comparison.compatibility_status],
                ["Reliability", f"{assessment.reliability.level.capitalize()} ({assessment.reliability.score}/100)"],
            ]
        ),
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
        Paragraph("Input summary", styles["Section"]),
        _input_table(request.borrower_input.model_dump()),
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
            Paragraph(DISCLAIMER, styles["Small"]),
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
