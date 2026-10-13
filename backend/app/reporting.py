from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

def build_pdf(result: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Subtle", parent=styles["BodyText"], textColor=colors.HexColor("#526078"), fontSize=9, leading=13))
    story = [
        Paragraph("AI Venture Assessment System", styles["Title"]),
        Paragraph(escape(result.get("startup_name","Startup")), styles["Heading1"]),
        Paragraph(f"Industry: {escape(result.get('industry',''))}", styles["Subtle"]),
        Spacer(1, 8*mm)
    ]
    data = [
        ["Readiness score", f"{result.get('readiness_score',0)}/100"],
        ["Readiness category", result.get("score_band","—")],
        ["Checklist risk level", result.get("risk_level","—")],
        ["Growth potential indicator", f"{result.get('growth_potential_score','—')}/100 (heuristic)"],
        ["Model status", result.get("model_status","—")]
    ]
    table = Table(data, colWidths=[48*mm, 115*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E9E7FF")),
        ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#172033")),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#D4D9E4")),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),9),("PADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))
    story.extend([table, Spacer(1, 6*mm),
        Paragraph("Important limitation", styles["Heading2"]),
        Paragraph("A readiness score is a heuristic and is not the probability of startup success. A model trained on synthetic data is not a validated real-world forecast. This report is decision support, not investment advice.", styles["BodyText"]),
        Spacer(1, 4*mm)])
    explainability = result.get("explainability", {})
    story.append(Paragraph("Assessment explanation", styles["Heading2"]))
    story.append(Paragraph(escape(explainability.get("method", "Rule-based assessment explanation.")), styles["Subtle"]))
    for heading, key in [("Positive signals", "positive_signals"), ("Priority gaps", "priority_gaps")]:
        story.append(Paragraph(heading, styles["Heading3"]))
        for item in explainability.get(key, []):
            story.append(Paragraph("• " + escape(str(item)), styles["BodyText"]))
    model_explanation = explainability.get("model_explanation", {})
    story.append(Paragraph("Model explanation (SHAP)", styles["Heading3"]))
    story.append(Paragraph(escape(model_explanation.get("note", "SHAP explanation was not available for this assessment.")), styles["Subtle"]))
    if model_explanation.get("available"):
        for heading, key in [("Factors pushing model output higher", "top_positive"), ("Factors pushing model output lower", "top_negative")]:
            story.append(Paragraph(heading, styles["Heading3"]))
            items = model_explanation.get(key, [])
            if items:
                for item in items:
                    story.append(Paragraph("• " + escape(f"{item.get('feature', 'Feature')}: SHAP {item.get('impact', 0):+.6f}; entered value {item.get('input_value', '—')}"), styles["BodyText"]))
            else:
                story.append(Paragraph("No contributions in this direction for this record.", styles["BodyText"]))
    financial = explainability.get("financial_snapshot", {})
    if financial:
        story.append(Paragraph("Financial snapshot", styles["Heading3"]))
        story.append(Paragraph(escape(f"Runway: {financial.get('runway_months', '—')} months | Net monthly burn (burn minus revenue): {financial.get('monthly_net_burn', '—')} | Revenue covers burn: {financial.get('revenue_covers_burn', '—')} | Alert: {financial.get('runway_alert', '—')}"), styles["BodyText"]))
    story.append(Paragraph(escape(result.get("growth_score_note", "Growth indicator is heuristic only.")), styles["Subtle"]))
    story.append(Spacer(1, 3*mm))
    for heading, key in [("Risk flags","risk_flags"),("SWOT analysis","swot"),("Recommendations","recommendations")]:
        story.append(Paragraph(heading, styles["Heading2"]))
        value = result.get(key, [])
        if key == "swot":
            for subheading, items in value.items():
                story.append(Paragraph(escape(subheading.title()), styles["Heading3"]))
                story.append(Paragraph(" • ".join(escape(str(x)) for x in items), styles["BodyText"]))
        else:
            for item in value:
                story.append(Paragraph("• " + escape(str(item)), styles["BodyText"]))
                story.append(Spacer(1, 2*mm))
    doc.build(story)
    return buffer.getvalue()
