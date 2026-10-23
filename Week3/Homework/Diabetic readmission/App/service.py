"""Business rules: risk scoring, CSV row cleaning and metric calculations. No SQL here.

EDUCATIONAL PROTOTYPE: the scoring weights are learning assumptions, not clinically validated rules.
"""
from . import repository
from .errors import ImportDataError
from .models import EncounterCreate
REQUIRED_COLUMNS = ("encounter_id", "patient_nbr", "age", "time_in_hospital", "number_inpatient", "number_emergency", "number_outpatient", "num_medications", "num_lab_procedures", "num_procedures", "admission_type_id", "discharge_disposition_id", "readmitted")
INT_COLUMNS = ("encounter_id", "patient_nbr", "time_in_hospital", "number_inpatient", "number_emergency", "number_outpatient", "num_medications", "num_lab_procedures", "num_procedures", "admission_type_id", "discharge_disposition_id")
NULL_LIKE = {"", "?", "NULL", "NA", "N/A", "NAN"}
# (field, threshold, points, reason)
RISK_RULES = (
    ("number_inpatient", 3, 3, "3+ prior inpatient visits"),
    ("number_emergency", 2, 2, "2+ emergency visits"),
    ("number_outpatient", 3, 1, "3+ outpatient visits"),
    ("time_in_hospital", 7, 1, "7+ days in hospital"),
    ("num_medications", 20, 1, "20+ medications"),
)
OUTCOME_NOTE = "The historical readmitted field is used only for retrospective validation and is not used in risk scoring."

def calculate_risk(encounter: dict) -> dict:
    """Return risk_score, risk_level and review_reason for one encounter.

    DATA LEAKAGE RULE: `readmitted` is the historical outcome and must NEVER be read here.
    """
    score, reasons = 0, []
    for field, threshold, points, reason in RISK_RULES:
        if (encounter.get(field) or 0) >= threshold:
            score += points
            reasons.append(reason)
    level = "HIGH" if score >= 5 else "MEDIUM" if score >= 3 else "LOW"
    return {"risk_score": score, "risk_level": level, "review_reason": "; ".join(reasons) or "No prioritization rules triggered"}

def create_encounter(encounter: EncounterCreate) -> dict:
    """Calculate the risk fields and persist a new encounter."""
    values = encounter.model_dump()
    return repository.create_encounter({**values, **calculate_risk(values)})

def validate_columns(header: list) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in (header or [])]
    if missing: raise ImportDataError(f"CSV is missing required columns: {', '.join(missing)}")

def _clean_text(value):
    value = (value or "").strip()
    return None if value.upper() in NULL_LIKE else value

def parse_encounter_row(row: dict, line_number: int) -> dict:
    """Clean one CSV row (null-like values become None, never invented) and attach its risk."""
    parsed = {}
    for column in INT_COLUMNS:
        text = _clean_text(row.get(column))
        try: parsed[column] = None if text is None else int(text)
        except ValueError: raise ImportDataError(f"Line {line_number}: column '{column}' has a non-numeric value {text!r}") from None
    for column in ("encounter_id", "patient_nbr"):
        if parsed[column] is None: raise ImportDataError(f"Line {line_number}: column '{column}' is required but blank")
    parsed["age"] = _clean_text(row.get("age"))
    parsed["readmitted"] = _clean_text(row.get("readmitted"))
    return {**parsed, **calculate_risk(parsed)}

def percentage(part: int, whole: int) -> float:
    return round(part * 100 / whole, 2) if whole else 0.0

def build_operations_summary(counts: dict, status_rows: list) -> dict:
    by_status = {row["status"]: row["count"] for row in status_rows}
    return {
        "total_encounters": counts["total_encounters"], "high_risk": counts["high_risk"], "medium_risk": counts["medium_risk"], "low_risk": counts["low_risk"],
        "pending_interventions": by_status.get("PENDING_REVIEW", 0), "assigned_interventions": by_status.get("ASSIGNED", 0), "contacted_interventions": by_status.get("CONTACTED", 0),
        "follow_up_scheduled": by_status.get("FOLLOW_UP_SCHEDULED", 0), "closed_interventions": by_status.get("CLOSED", 0),
    }

def _group_totals(group_rows: list) -> dict:
    totals = {level: (0, 0) for level in ("HIGH", "MEDIUM", "LOW")}
    for row in group_rows: totals[row["risk_level"]] = (row["encounters"], row["readmitted_under_30"])
    return totals

def build_readmission_analysis(group_rows: list) -> dict:
    """Compare already-assigned risk groups with the historical <30 outcome. Rates differing does not prove the rules are predictive."""
    totals = _group_totals(group_rows)
    all_count = sum(count for count, _ in totals.values())
    all_readmitted = sum(readmitted for _, readmitted in totals.values())
    result = {"overall_encounters": all_count, "overall_readmitted_under_30_days": all_readmitted, "overall_readmission_rate": percentage(all_readmitted, all_count)}
    for level, (count, readmitted) in totals.items():
        prefix = f"{level.lower()}_risk"
        result[f"{prefix}_patients"] = count
        result[f"{prefix}_readmitted_under_30_days"] = readmitted
        result[f"{prefix}_readmission_rate"] = percentage(readmitted, count)
    result["note"] = OUTCOME_NOTE
    return result

def build_management_dashboard(group_rows: list, pending: int) -> dict:
    totals = _group_totals(group_rows)
    all_count = sum(count for count, _ in totals.values())
    all_readmitted = sum(readmitted for _, readmitted in totals.values())
    high_count, high_readmitted = totals["HIGH"]
    return {
        "total_diabetes_encounters": all_count, "readmitted_under_30_days": all_readmitted, "readmission_rate": percentage(all_readmitted, all_count),
        "high_risk_population": high_count, "high_risk_percent": percentage(high_count, all_count), "high_risk_30_day_readmissions": high_readmitted, "care_queue_pending": pending,
    }
