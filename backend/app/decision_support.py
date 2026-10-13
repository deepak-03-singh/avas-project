"""Deterministic portfolio-level alerts and historical assessment trends."""
import json
from collections import defaultdict
from datetime import datetime


def build_decision_support(assessments, portfolio_entries):
    portfolio_by_assessment = {entry.assessment_id: entry for entry in portfolio_entries}
    alerts = []
    history_by_name = defaultdict(list)
    risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Unknown": 0}

    for row in assessments:
        try:
            result = json.loads(row.result_json or "{}")
        except (TypeError, json.JSONDecodeError):
            result = {}
        risk = row.risk_level if row.risk_level in {"High", "Medium", "Low"} else "Unknown"
        risk_counts[risk] += 1
        history_by_name[row.startup_name.strip().casefold()].append({
            "id": row.id, "startup_name": row.startup_name,
            "industry": row.industry, "readiness_score": row.readiness_score,
            "risk_level": risk,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
        entry = portfolio_by_assessment.get(row.id)
        financial = ((result.get("explainability") or {}).get("financial_snapshot") or {})
        runway = financial.get("runway_months")
        if risk == "High":
            alerts.append({"priority": "High", "type": "High risk", "assessment_id": row.id,
                           "startup_name": row.startup_name, "message": "Review major risk flags and verify supporting evidence."})
        if isinstance(runway, (int, float)) and runway < 6:
            alerts.append({"priority": "High" if runway < 3 else "Medium", "type": "Short runway",
                           "assessment_id": row.id, "startup_name": row.startup_name,
                           "message": f"Recorded runway is {runway:g} months; validate cash and funding assumptions."})
        if row.readiness_score < 50:
            alerts.append({"priority": "Medium", "type": "Low readiness", "assessment_id": row.id,
                           "startup_name": row.startup_name, "message": "Address the highest-priority gaps before making a decision."})
        if entry and entry.status == "Due diligence":
            gaps = ((result.get("explainability") or {}).get("priority_gaps") or [])
            if gaps:
                alerts.append({"priority": "Medium", "type": "Diligence follow-up", "assessment_id": row.id,
                               "startup_name": row.startup_name,
                               "message": str(gaps[0])[:240]})

    trends = []
    for snapshots in history_by_name.values():
        snapshots.sort(key=lambda item: (item["created_at"] or "", item["id"]))
        if len(snapshots) < 2:
            continue
        first, latest = snapshots[0], snapshots[-1]
        delta = latest["readiness_score"] - first["readiness_score"]
        trends.append({"startup_name": latest["startup_name"], "assessment_count": len(snapshots),
                       "first_score": first["readiness_score"], "latest_score": latest["readiness_score"],
                       "score_change": delta, "direction": "Improved" if delta > 0 else "Declined" if delta < 0 else "Unchanged",
                       "snapshots": snapshots})
    trends.sort(key=lambda item: item["startup_name"].casefold())
    alerts.sort(key=lambda item: (0 if item["priority"] == "High" else 1, item["startup_name"].casefold(), item["type"]))
    portfolio_count = len(portfolio_entries)
    avg = round(sum(e.readiness_score for e in portfolio_entries) / portfolio_count, 1) if portfolio_count else None
    status_counts = {}
    for entry in portfolio_entries:
        status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
    return {
        "summary": {"assessments_count": len(assessments), "portfolio_count": portfolio_count,
                    "average_portfolio_readiness": avg, "high_risk_count": risk_counts["High"],
                    "alerts_count": len(alerts), "trend_count": len(trends)},
        "risk_distribution": risk_counts,
        "portfolio_status_counts": status_counts,
        "alerts": alerts,
        "trends": trends,
        "notice": "Alerts are deterministic screening prompts based on saved assessment fields, not predictions of failure or investment advice. Trends compare assessments with the same startup name; confirm that they refer to the same business and consistent inputs."
    }
