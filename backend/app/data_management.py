"""Validation helpers for portable AVAS assessment backups."""
from typing import Any


def validate_assessment_backup(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("format") != "avas-assessment-backup" or payload.get("schema_version") != 1:
        raise ValueError("Unsupported backup format or schema version.")
    items = payload.get("assessments")
    if not isinstance(items, list):
        raise ValueError("Backup must contain an assessments list.")
    if len(items) > 500:
        raise OverflowError("A maximum of 500 assessments can be imported at once.")
    prepared: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        label = f"Assessment record {index + 1}"
        if not isinstance(item, dict):
            raise ValueError(f"{label} is invalid.")
        name, industry = item.get("startup_name"), item.get("industry")
        score, risk, result = item.get("readiness_score"), item.get("risk_level"), item.get("result")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            raise ValueError(f"{label} has an invalid startup name.")
        if not isinstance(industry, str) or not industry.strip() or len(industry.strip()) > 100:
            raise ValueError(f"{label} has an invalid industry.")
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError(f"{label} has an invalid readiness score.")
        if risk not in {"Low", "Medium", "High", "Unknown"}:
            raise ValueError(f"{label} has an invalid risk level.")
        if not isinstance(result, dict):
            raise ValueError(f"{label} is missing its result object.")
        result = dict(result)
        result.update({"startup_name": name.strip(), "industry": industry.strip(),
                       "readiness_score": score, "risk_level": risk})
        prepared.append({"startup_name": name.strip(), "industry": industry.strip(),
                         "readiness_score": score, "risk_level": risk, "result": result})
    return prepared
