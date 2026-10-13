from app.pitch_deck import analyze_pitch_text

def test_detects_common_sections_and_questions():
    text = "Problem: farmers need better tools. Our product platform is a solution. Market size TAM and SAM. Business model subscription pricing. Founders team has traction with 200 customers. Competitor analysis. Financial projections and burn rate. Funding ask use of funds."
    result = analyze_pitch_text(text, 3)
    assert result["page_count"] == 3
    assert "Problem" in result["detected_sections"]
    assert "Business model" in result["detected_sections"]
    assert result["evidence_coverage_percent"] > 0

def test_missing_sections_are_flagged():
    result = analyze_pitch_text("We are building a small mobile application for students.", 1)
    assert "Market opportunity" in result["sections_to_review"]
    assert result["founder_questions"]
    assert "not a startup quality or success score" in result["coverage_note"]
