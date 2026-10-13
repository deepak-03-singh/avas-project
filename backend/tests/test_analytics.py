from datetime import datetime, timezone
from types import SimpleNamespace
from app.analytics import build_analytics


def row(id, name, industry, score, risk, month):
    return SimpleNamespace(id=id, startup_name=name, industry=industry, readiness_score=score,
                           risk_level=risk, created_at=datetime.fromisoformat(month).replace(tzinfo=timezone.utc))


def test_analytics_aggregates_assessments():
    result = build_analytics([
        row(1, "Alpha", "FinTech", 80, "Low", "2026-01-10T10:00:00"),
        row(2, "Beta", "FinTech", 60, "High", "2026-01-12T10:00:00"),
        row(3, "Gamma", "HealthTech", 40, "Medium", "2026-02-12T10:00:00"),
    ])
    assert result["summary"]["total_assessments"] == 3
    assert result["summary"]["average_readiness"] == 60
    assert result["summary"]["high_risk_count"] == 1
    assert result["industry_comparison"][0] == {"industry": "FinTech", "count": 2, "average_score": 70}
    assert result["monthly_trend"][0]["month"] == "2026-01"
    assert sum(x["count"] for x in result["score_distribution"]) == 3


def test_analytics_empty_data_is_safe():
    result = build_analytics([])
    assert result["summary"]["total_assessments"] == 0
    assert result["summary"]["average_readiness"] == 0
    assert result["assessments"] == []


def test_advanced_analytics_includes_financials_and_normalized_factors():
    import json
    saved = row(4, "Delta", "ClimateTech", 75, "Low", "2026-03-01T10:00:00")
    saved.result_json = json.dumps({"input_snapshot": {
        "monthly_revenue": 12000, "monthly_burn": 18000,
        "funding_needed": 50000, "financial_runway_months": 8,
        "problem_clarity": 4, "solution_differentiation": 3,
        "has_prototype": True, "has_competitor_research": False
    }})
    result = build_analytics([saved])
    financial = result["financial_summary"]
    assert financial["records_with_financial_inputs"] == 1
    assert financial["average_monthly_revenue"] == 12000
    assert financial["average_monthly_burn"] == 18000
    assert financial["revenue_covers_burn_count"] == 0
    assert financial["records"][0]["net_burn"] == 6000
    factors = {item["factor"]: item["average_score"] for item in result["readiness_factors"]}
    assert factors["Problem clarity"] == 75
    assert factors["Prototype available"] == 100
    assert factors["Competitor research"] == 0


def test_advanced_analytics_handles_legacy_records_without_snapshots():
    result = build_analytics([row(1, "Legacy", "Other", 50, "Medium", "2025-12-01T10:00:00")])
    assert result["financial_summary"]["records_with_financial_inputs"] == 0
    assert result["financial_summary"]["average_monthly_revenue"] is None
    assert result["readiness_factors"] == []
