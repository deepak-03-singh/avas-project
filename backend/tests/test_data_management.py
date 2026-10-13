import pytest
from app.data_management import validate_assessment_backup


def payload(records=None):
    return {"format": "avas-assessment-backup", "schema_version": 1,
            "assessments": records if records is not None else [{
                "startup_name": "  GreenCart ", "industry": "ClimateTech", "readiness_score": 76,
                "risk_level": "Medium", "result": {"old_id": 999, "readiness_score": 2}
            }]}


def test_backup_validation_normalizes_fields_and_overrides_conflicting_result_summary():
    item = validate_assessment_backup(payload())[0]
    assert item["startup_name"] == "GreenCart"
    assert item["result"]["startup_name"] == "GreenCart"
    assert item["result"]["readiness_score"] == 76
    assert item["result"]["risk_level"] == "Medium"
    # Imported IDs are not used as database IDs; endpoint creates fresh rows.
    assert item["result"]["old_id"] == 999


def test_backup_validation_rejects_unsupported_version():
    data = payload(); data["schema_version"] = 99
    with pytest.raises(ValueError, match="Unsupported backup"):
        validate_assessment_backup(data)


def test_backup_validation_rejects_invalid_score_and_boolean_score():
    for score in (-1, 101, True, 77.5):
        data = payload(); data["assessments"][0]["readiness_score"] = score
        with pytest.raises(ValueError, match="readiness score"):
            validate_assessment_backup(data)


def test_backup_validation_caps_record_count():
    data = payload([{}] * 501)
    with pytest.raises(OverflowError, match="500"):
        validate_assessment_backup(data)


def test_backup_validation_allows_empty_backup():
    assert validate_assessment_backup(payload([])) == []
