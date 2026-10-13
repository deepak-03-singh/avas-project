"""Heuristic pitch-deck text review. This is not an LLM or investment recommendation."""
import re
from collections import OrderedDict

SECTION_RULES = OrderedDict([
    ("Problem", [r"\bproblem\b", r"pain point", r"challenge", r"customer need"]),
    ("Solution / Product", [r"\bsolution\b", r"product", r"platform", r"prototype", r"MVP"]),
    ("Market opportunity", [r"TAM", r"SAM", r"SOM", r"market size", r"target market", r"\bmarket opportunity\b"]),
    ("Business model", [r"business model", r"revenue model", r"pricing", r"subscription", r"\bmonetiz\w*\b"]),
    ("Traction / Validation", [r"traction", r"pilot", r"users", r"customers", r"retention", r"validation", r"growth rate"]),
    ("Competition", [r"competitor", r"competition", r"competitive advantage", r"differentiation", r"alternatives"]),
    ("Go-to-market", [r"go.to.market", r"customer acquisition", r"marketing strategy", r"distribution", r"sales strategy"]),
    ("Team", [r"founder", r"leadership team", r"our team", r"management team", r"co.founder"]),
    ("Financials", [r"financial projection", r"revenue forecast", r"profit and loss", r"cash flow", r"burn rate", r"unit economics", r"financials"]),
    ("Funding ask / Use of funds", [r"funding ask", r"raising", r"investment ask", r"use of funds", r"capital required", r"fundraise"]),
])

QUESTIONS = {
 "Problem": "Which customer segment experiences this problem most often, and what evidence confirms its severity?",
 "Solution / Product": "What can a user do in the product today, and what evidence shows it solves the stated problem?",
 "Market opportunity": "What sources, dates, and assumptions support the TAM/SAM/SOM estimates?",
 "Business model": "Who pays, how much do they pay, and what gross margin or unit economics are expected?",
 "Traction / Validation": "Which traction metrics are measured, over what period, and how many customers are paying?",
 "Competition": "Which direct and indirect alternatives do customers use, and why would they switch?",
 "Go-to-market": "Which acquisition channels will be tested first, and what CAC and conversion assumptions apply?",
 "Team": "Which critical skills or roles are missing, and how will the team fill those gaps?",
 "Financials": "What assumptions drive the forecast, monthly burn, runway, and break-even timeline?",
 "Funding ask / Use of funds": "How much funding is requested, what milestones will it finance, and how long will it last?",
}

def analyze_pitch_text(text: str, page_count: int = 0) -> dict:
    cleaned = re.sub(r"[\t\r]+", " ", text or "")
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n{1,}|(?<=[.!?])\s{2,}", cleaned) if p.strip()]
    lower = cleaned.lower()
    sections=[]
    found=[]
    missing=[]
    for name, patterns in SECTION_RULES.items():
        hits=[p for p in patterns if re.search(p, cleaned, re.I)]
        matched=bool(hits)
        (found if matched else missing).append(name)
        evidence=None
        if matched:
            candidates=[]
            for para in paragraphs:
                if any(re.search(p, para, re.I) for p in patterns):
                    candidates.append(para)
            evidence=(candidates[0][:300] + ("…" if len(candidates[0])>300 else "")) if candidates else None
        sections.append({"name":name,"status":"found" if matched else "not_detected","evidence":evidence})
    questions=[QUESTIONS[n] for n in missing[:6]]
    coverage=round(len(found)/len(SECTION_RULES)*100)
    return {
        "document_type":"PDF pitch deck", "page_count":page_count, "characters_extracted":len(cleaned),
        "evidence_coverage_percent":coverage, "coverage_note":"Heuristic coverage of common pitch-deck topics; not a startup quality or success score.",
        "sections":sections,"detected_sections":found,"sections_to_review":missing,"founder_questions":questions,
        "warnings":["This review uses keyword and text-pattern checks, not an expert judgement or generative AI.","Text-only extraction cannot read text embedded in images. OCR is not included.","A section marked not detected may still be present under different wording; review the PDF manually."],
        "text_preview":cleaned[:1200]
    }
