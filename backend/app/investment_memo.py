"""Deterministic investment memo builder based only on saved AVAS assessment data."""
from io import BytesIO
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

LIMITATION = (
    "This memo is generated from self-reported assessment inputs and rule-based AVAS outputs. "
    "It is not independent due diligence, audited financial analysis, investment advice, or a forecast of success. "
    "Verify claims with original documents and qualified professionals."
)

def build_memo(result: dict, assessment_id: int, created_at: str | None = None) -> dict:
    explain = result.get("explainability") or {}
    financial = explain.get("financial_snapshot") or {}
    snapshot = result.get("input_snapshot") or {}
    swot = result.get("swot") or {}
    gaps = [
        "Validate revenue, expenses, cash balance and runway against current financial statements or bank records.",
        "Request customer evidence (contracts, invoices, retention/cohort data) to substantiate traction claims.",
        "Validate total addressable market and competitor claims with independent, dated sources.",
        "Review founder background, ownership/cap-table, legal status, IP ownership and regulatory obligations.",
    ]
    if not snapshot:
        gaps.append("This assessment predates Phase 10 and does not retain a full input snapshot; re-run the assessment to include more financial details.")
    score = result.get("readiness_score")
    risk = result.get("risk_level", "Not available")
    if isinstance(score, (int, float)):
        if score >= 70:
            summary = f"{result.get('startup_name', 'The venture')} has a readiness score of {score}/100 and a checklist risk level of {risk.lower()}. Treat this as an initial screening signal, not an investment decision."
        elif score >= 45:
            summary = f"{result.get('startup_name', 'The venture')} has a readiness score of {score}/100 and a checklist risk level of {risk.lower()}. Further validation is recommended before drawing conclusions."
        else:
            summary = f"{result.get('startup_name', 'The venture')} has a readiness score of {score}/100 and a checklist risk level of {risk.lower()}. Prioritize the listed gaps and validate core assumptions before reassessment."
    else:
        summary = "The saved assessment contains limited score information. Review the source assessment before using this memo."
    return {
        "assessment_id": assessment_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assessment_created_at": created_at,
        "startup_name": result.get("startup_name", "Startup"),
        "industry": result.get("industry", "Not provided"),
        "executive_summary": summary,
        "assessment_snapshot": {
            "readiness_score": score,
            "score_band": result.get("score_band", "Not available"),
            "risk_level": risk,
            "growth_potential_indicator": result.get("growth_potential_score"),
            "model_status": result.get("model_status", "Not available"),
        },
        "financial_overview": {
            "monthly_revenue": snapshot.get("monthly_revenue"),
            "monthly_burn": snapshot.get("monthly_burn"),
            "funding_needed": snapshot.get("funding_needed"),
            "runway_months": financial.get("runway_months", snapshot.get("financial_runway_months")),
            "monthly_net_burn": financial.get("monthly_net_burn"),
            "revenue_covers_burn": financial.get("revenue_covers_burn"),
            "currency_note": "Currency was not independently verified; confirm that all entered figures use the same currency and period.",
        },
        "positive_signals": list(explain.get("positive_signals") or []),
        "priority_gaps": list(explain.get("priority_gaps") or []),
        "risk_flags": list(result.get("risk_flags") or []),
        "swot": {k: list(v or []) for k, v in swot.items() if k in {"strengths", "weaknesses", "opportunities", "threats"}},
        "recommendations": list(result.get("recommendations") or []),
        "evidence_gaps": gaps,
        "limitations": LIMITATION,
    }

def build_investment_memo_pdf(memo: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="MemoSubtle", parent=styles["BodyText"], textColor=colors.HexColor("#536078"), fontSize=8.5, leading=12))
    styles.add(ParagraphStyle(name="MemoSmall", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=3))
    story = [Paragraph("AVAS | INVESTMENT MEMO", styles["Title"]),
             Paragraph(escape(str(memo.get("startup_name", "Startup"))), styles["Heading1"]),
             Paragraph(f"Industry: {escape(str(memo.get('industry', 'Not provided')))} · Assessment ID: {memo.get('assessment_id', '—')}", styles["MemoSubtle"]),
             Spacer(1, 5*mm)]
    story += [Paragraph("1. Executive summary", styles["Heading2"]), Paragraph(escape(str(memo.get("executive_summary", "Not available"))), styles["BodyText"]), Spacer(1, 3*mm)]
    snap = memo.get("assessment_snapshot", {})
    fin = memo.get("financial_overview", {})
    rows = [["Readiness score", f"{snap.get('readiness_score', '—')}/100"], ["Score band", snap.get("score_band") or "—"],
            ["Checklist risk", snap.get("risk_level") or "—"], ["Growth indicator", f"{snap.get('growth_potential_indicator', '—')}/100"],
            ["Runway", f"{fin.get('runway_months', 'Not recorded')} months"],
            ["Monthly net burn (burn − revenue)", fin.get("monthly_net_burn", "Not recorded")],
            ["Monthly revenue entered", fin.get("monthly_revenue", "Not recorded")],
            ["Monthly burn entered", fin.get("monthly_burn", "Not recorded")],
            ["Funding required entered", fin.get("funding_needed", "Not recorded")]]
    table = Table([[Paragraph(escape(str(a)), styles["MemoSmall"]), Paragraph(escape(str(b)), styles["MemoSmall"])] for a,b in rows], colWidths=[65*mm, 95*mm], repeatRows=0)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EAE8FF")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#D2D8E5")),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),6)]))
    story += [Paragraph("2. Assessment and financial overview", styles["Heading2"]), table, Paragraph(escape(fin.get("currency_note", "")), styles["MemoSubtle"]), Spacer(1, 3*mm)]
    def bullet_section(title, items):
        block = [Paragraph(escape(title), styles["Heading2"])]
        if items:
            block.extend(Paragraph("• " + escape(str(item)), styles["MemoSmall"]) for item in items)
        else:
            block.append(Paragraph("No items were stored for this section.", styles["MemoSubtle"]))
        return block
    story += bullet_section("3. Positive signals", memo.get("positive_signals", []))
    story += bullet_section("4. Priority gaps and risk flags", list(memo.get("priority_gaps", [])) + list(memo.get("risk_flags", [])))
    swot = memo.get("swot", {})
    story.append(Paragraph("5. SWOT snapshot", styles["Heading2"]))
    for key in ("strengths", "weaknesses", "opportunities", "threats"):
        story.append(Paragraph(escape(key.title()), styles["Heading3"]))
        story.extend(Paragraph("• " + escape(str(item)), styles["MemoSmall"]) for item in swot.get(key, []))
    story += bullet_section("6. Recommended next steps", memo.get("recommendations", []))
    story += bullet_section("7. Evidence gaps / due diligence checklist", memo.get("evidence_gaps", []))
    story += [Spacer(1, 3*mm), Paragraph("Limitations and use", styles["Heading2"]), Paragraph(escape(str(memo.get("limitations", LIMITATION))), styles["MemoSubtle"]),
              Spacer(1, 2*mm), Paragraph("Generated by AVAS from saved assessment data. Figures and claims have not been independently verified.", styles["MemoSubtle"])]
    doc.build(story)
    return buffer.getvalue()
