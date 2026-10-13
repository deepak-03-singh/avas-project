"""Account-scoped analytics helpers for saved AVAS assessments."""
from collections import Counter, defaultdict
import json

FACTOR_FIELDS = [
    ("problem_clarity", "Problem clarity", "rating"),
    ("solution_differentiation", "Solution differentiation", "rating"),
    ("market_demand", "Market demand", "rating"),
    ("competition_intensity", "Competition intensity", "rating"),
    ("founder_experience", "Founder experience", "rating"),
    ("team_completeness", "Team completeness", "rating"),
    ("traction_level", "Traction level", "rating"),
    ("revenue_model_clarity", "Revenue model clarity", "rating"),
    ("has_prototype", "Prototype available", "boolean"),
    ("has_competitor_research", "Competitor research", "boolean"),
]


def _safe_number(value):
    try:
        number = float(value)
        return number if number >= 0 else None
    except (TypeError, ValueError):
        return None


def build_analytics(rows):
    records = []
    financial_records = []
    factor_buckets = defaultdict(list)
    for row in rows:
        created = row.created_at.isoformat() if row.created_at else None
        try:
            result = json.loads(getattr(row, "result_json", "{}") or "{}")
            snapshot = result.get("input_snapshot") or {}
        except (TypeError, json.JSONDecodeError):
            result, snapshot = {}, {}
        records.append({
            "id": row.id, "startup_name": row.startup_name,
            "industry": row.industry or "Unspecified",
            "readiness_score": int(row.readiness_score or 0),
            "risk_level": (row.risk_level or "Unknown").title(),
            "created_at": created,
        })
        if snapshot:
            revenue = _safe_number(snapshot.get("monthly_revenue"))
            burn = _safe_number(snapshot.get("monthly_burn"))
            funding = _safe_number(snapshot.get("funding_needed"))
            runway = _safe_number(snapshot.get("financial_runway_months"))
            financial_records.append({
                "id": row.id, "startup_name": row.startup_name,
                "industry": row.industry or "Unspecified", "created_at": created,
                "monthly_revenue": revenue, "monthly_burn": burn,
                "funding_needed": funding, "runway_months": runway,
                "net_burn": max((burn or 0) - (revenue or 0), 0) if burn is not None and revenue is not None else None,
                "revenue_covers_burn": revenue >= burn if revenue is not None and burn is not None else None,
            })
            for key, label, kind in FACTOR_FIELDS:
                value = snapshot.get(key)
                if kind == "rating":
                    number = _safe_number(value)
                    if number is not None and 1 <= number <= 5:
                        factor_buckets[(key, label)].append((number - 1) * 25)
                elif value is not None:
                    factor_buckets[(key, label)].append(100 if bool(value) else 0)

    count = len(records)
    avg = round(sum(r["readiness_score"] for r in records) / count, 1) if count else 0
    risk_counts = Counter(r["risk_level"] for r in records)
    industry_buckets, month_buckets = defaultdict(list), defaultdict(list)
    for row in records:
        industry_buckets[row["industry"]].append(row["readiness_score"])
        month = row["created_at"][:7] if row["created_at"] else "Unknown"
        month_buckets[month].append(row["readiness_score"])
    industry = [{"industry": key, "count": len(vals), "average_score": round(sum(vals)/len(vals), 1)}
                for key, vals in industry_buckets.items()]
    industry.sort(key=lambda x: (-x["count"], x["industry"].lower()))
    trend = [{"month": key, "assessments": len(vals), "average_score": round(sum(vals)/len(vals), 1)}
             for key, vals in sorted(month_buckets.items())]
    ranges = [("0–39", 0, 39), ("40–59", 40, 59), ("60–79", 60, 79), ("80–100", 80, 100)]
    distribution = [{"range": label, "count": sum(low <= r["readiness_score"] <= high for r in records)}
                    for label, low, high in ranges]

    def average(key):
        values = [item[key] for item in financial_records if item.get(key) is not None]
        return round(sum(values) / len(values), 2) if values else None

    runway_bands = [
        {"range": "0–3 months", "count": sum(0 <= x["runway_months"] <= 3 for x in financial_records if x["runway_months"] is not None)},
        {"range": "4–6 months", "count": sum(3 < x["runway_months"] <= 6 for x in financial_records if x["runway_months"] is not None)},
        {"range": "7–12 months", "count": sum(6 < x["runway_months"] <= 12 for x in financial_records if x["runway_months"] is not None)},
        {"range": "12+ months", "count": sum(x["runway_months"] > 12 for x in financial_records if x["runway_months"] is not None)},
    ]
    return {
        "summary": {"total_assessments": count, "average_readiness": avg,
                    "high_risk_count": risk_counts.get("High", 0),
                    "low_risk_count": risk_counts.get("Low", 0),
                    "medium_risk_count": risk_counts.get("Medium", 0)},
        "risk_distribution": [{"risk_level": key, "count": risk_counts.get(key, 0)}
                              for key in ["Low", "Medium", "High", "Unknown"] if risk_counts.get(key, 0)],
        "industry_comparison": industry[:12], "score_distribution": distribution,
        "monthly_trend": trend[-12:], "assessments": records,
        "readiness_factors": [{"factor": label, "average_score": round(sum(values)/len(values), 1), "sample_count": len(values)}
                              for (_, label), values in factor_buckets.items() if values],
        "financial_summary": {
            "records_with_financial_inputs": len(financial_records),
            "average_monthly_revenue": average("monthly_revenue"),
            "average_monthly_burn": average("monthly_burn"),
            "average_funding_needed": average("funding_needed"),
            "average_runway_months": average("runway_months"),
            "revenue_covers_burn_count": sum(x["revenue_covers_burn"] is True for x in financial_records),
            "revenue_exceeds_burn_count": sum(x["revenue_covers_burn"] is False for x in financial_records),
            "runway_distribution": runway_bands,
            "records": financial_records[-30:],
        },
        "notice": "Analytics use only assessments saved to your account. Financial inputs may be missing from older records; missing values are excluded rather than guessed. Scores are rubric-based decision-support signals, not validated forecasts."
    }
