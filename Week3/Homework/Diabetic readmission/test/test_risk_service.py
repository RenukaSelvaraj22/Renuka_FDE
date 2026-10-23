import pytest
from app.errors import ImportDataError
from app.service import build_readmission_analysis, calculate_risk, parse_encounter_row, percentage, validate_columns

def encounter(**overrides): return {"number_inpatient": 0, "number_emergency": 0, "number_outpatient": 0, "time_in_hospital": 2, "num_medications": 5, **overrides}

def test_low_risk():
    result = calculate_risk(encounter())
    assert (result["risk_score"], result["risk_level"]) == (0, "LOW")

def test_medium_risk():
    result = calculate_risk(encounter(number_inpatient=3))
    assert (result["risk_score"], result["risk_level"]) == (3, "MEDIUM")
    assert result["review_reason"] == "3+ prior inpatient visits"

def test_high_risk():
    result = calculate_risk(encounter(number_inpatient=3, number_emergency=2))
    assert (result["risk_score"], result["risk_level"]) == (5, "HIGH")
    assert "2+ emergency visits" in result["review_reason"]

def test_score_boundaries():
    assert calculate_risk(encounter(number_emergency=2))["risk_level"] == "LOW"
    assert calculate_risk(encounter(number_emergency=2, time_in_hospital=7))["risk_level"] == "MEDIUM"
    assert calculate_risk(encounter(number_inpatient=3, time_in_hospital=7, num_medications=20))["risk_level"] == "HIGH"

def test_readmitted_does_not_change_risk():
    """Leakage guard: the historical outcome must not influence the score."""
    base = encounter(number_inpatient=3, number_emergency=1)
    results = [calculate_risk({**base, "readmitted": value}) for value in ("<30", ">30", "NO", None)]
    assert all(result == results[0] for result in results)

def test_missing_values_count_as_zero():
    assert calculate_risk({"number_inpatient": None})["risk_level"] == "LOW"

def test_parse_row_handles_null_like_values():
    row = {"encounter_id": "10", "patient_nbr": "5", "age": "?", "time_in_hospital": "8", "number_inpatient": "", "number_emergency": "0", "number_outpatient": "0", "num_medications": "21", "num_lab_procedures": "?", "num_procedures": "0", "admission_type_id": "1", "discharge_disposition_id": "1", "readmitted": "<30"}
    parsed = parse_encounter_row(row, 2)
    assert parsed["age"] is None and parsed["number_inpatient"] is None and parsed["num_lab_procedures"] is None
    assert (parsed["risk_score"], parsed["risk_level"], parsed["readmitted"]) == (2, "LOW", "<30")

def test_parse_row_rejects_malformed_number():
    row = {"encounter_id": "abc", "patient_nbr": "5"}
    with pytest.raises(ImportDataError, match="Line 7"): parse_encounter_row(row, 7)

def test_validate_columns_lists_missing():
    with pytest.raises(ImportDataError, match="readmitted"): validate_columns(["encounter_id", "patient_nbr"])

def test_percentage_handles_zero_division():
    assert percentage(1, 0) == 0.0
    assert percentage(1, 3) == 33.33

def test_readmission_analysis_rates():
    rows = [{"risk_level": "HIGH", "encounters": 4, "readmitted_under_30": 1}, {"risk_level": "LOW", "encounters": 6, "readmitted_under_30": 0}]
    result = build_readmission_analysis(rows)
    assert result["high_risk_readmission_rate"] == 25.0 and result["medium_risk_patients"] == 0 and result["overall_readmission_rate"] == 10.0
