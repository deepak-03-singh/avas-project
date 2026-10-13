from app.schemas import CompareInput

def test_compare_input_accepts_two_to_four_ids():
    assert CompareInput(assessment_ids=[1, 2]).assessment_ids == [1, 2]
    assert CompareInput(assessment_ids=[1, 2, 3, 4]).assessment_ids == [1, 2, 3, 4]

def test_compare_input_rejects_more_than_four_ids():
    try:
        CompareInput(assessment_ids=[1, 2, 3, 4, 5])
    except Exception:
        pass
    else:
        raise AssertionError("expected validation failure")
