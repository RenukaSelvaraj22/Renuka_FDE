"""All SQL lives here. Every value is passed as a psycopg parameter (%s); only fixed SQL fragments are ever joined into a query."""
import psycopg
from .database import get_connection
from .errors import DuplicateEncounterError
ENCOUNTER_COLUMNS = ("encounter_id", "patient_nbr", "age", "time_in_hospital", "number_inpatient", "number_emergency", "number_outpatient", "num_medications", "num_lab_procedures", "num_procedures", "admission_type_id", "discharge_disposition_id", "readmitted", "risk_score", "risk_level", "review_reason")
QUEUE_SELECT = """
    SELECT e.encounter_id, e.patient_nbr, e.age, e.risk_score, e.risk_level, e.review_reason,
           ci.intervention_id, ci.status, ci.assigned_to, ci.notes, ci.created_at, ci.updated_at
    FROM care_interventions ci
    JOIN patient_encounters e ON e.encounter_id = ci.encounter_id
"""

def _fetch_all(query, params=()):
    with get_connection() as conn: return conn.execute(query, params).fetchall()

def _fetch_one(query, params=()):
    with get_connection() as conn: return conn.execute(query, params).fetchone()

def _where(clauses: list) -> str:
    return f"WHERE {' AND '.join(clauses)}" if clauses else ""

def list_encounters(risk_level, readmitted, limit, offset):
    clauses, params = [], []
    if risk_level: clauses.append("risk_level = %s"); params.append(risk_level)
    if readmitted: clauses.append("readmitted = %s"); params.append(readmitted)
    return _fetch_all(f"SELECT * FROM patient_encounters {_where(clauses)} ORDER BY encounter_id LIMIT %s OFFSET %s", (*params, limit, offset))

def get_encounter(encounter_id):
    return _fetch_one("""
        SELECT e.*, ci.intervention_id, ci.status AS intervention_status, ci.assigned_to, ci.notes AS intervention_notes,
               ci.created_at AS intervention_created_at, ci.updated_at AS intervention_updated_at
        FROM patient_encounters e
        LEFT JOIN care_interventions ci ON ci.encounter_id = e.encounter_id
        WHERE e.encounter_id = %s
    """, (encounter_id,))

def list_care_queue(risk_level, status, assigned_to, limit, offset):
    clauses, params = ["e.risk_level IN ('MEDIUM', 'HIGH')"], []
    if risk_level: clauses.append("e.risk_level = %s"); params.append(risk_level)
    if status: clauses.append("ci.status = %s"); params.append(status)
    if assigned_to: clauses.append("ci.assigned_to = %s"); params.append(assigned_to)
    order = "ORDER BY CASE e.risk_level WHEN 'HIGH' THEN 0 ELSE 1 END, ci.created_at, ci.intervention_id"
    return _fetch_all(f"{QUEUE_SELECT} {_where(clauses)} {order} LIMIT %s OFFSET %s", (*params, limit, offset))

def update_intervention(encounter_id, status, assigned_to, notes):
    """Returns the updated row, or None when the encounter has no intervention. Fields left as None are kept unchanged."""
    return _fetch_one("""
        UPDATE care_interventions
        SET status = COALESCE(%s, status), assigned_to = COALESCE(%s, assigned_to), notes = COALESCE(%s, notes), updated_at = CURRENT_TIMESTAMP
        WHERE encounter_id = %s
        RETURNING intervention_id, encounter_id, status, assigned_to, notes, created_at, updated_at
    """, (status, assigned_to, notes, encounter_id))

def create_encounter(encounter):
    """Insert a scored encounter and queue it when its risk level requires review."""
    columns = ENCOUNTER_COLUMNS
    query = f"""
        INSERT INTO patient_encounters ({', '.join(columns)})
        VALUES ({', '.join(f'%({column})s' for column in columns)})
        RETURNING *
    """
    try:
        with get_connection() as conn:
            created = conn.execute(query, encounter).fetchone()
            if encounter["risk_level"] != "LOW":
                conn.execute(
                    "INSERT INTO care_interventions (encounter_id) VALUES (%s)",
                    (encounter["encounter_id"],),
                )
            return created
    except psycopg.errors.UniqueViolation as exc:
        raise DuplicateEncounterError(
            f"Encounter {encounter['encounter_id']} already exists"
        ) from exc

def get_risk_counts():
    return _fetch_one("""
        SELECT COUNT(*) AS total_encounters,
               COUNT(*) FILTER (WHERE risk_level = 'HIGH') AS high_risk,
               COUNT(*) FILTER (WHERE risk_level = 'MEDIUM') AS medium_risk,
               COUNT(*) FILTER (WHERE risk_level = 'LOW') AS low_risk
        FROM patient_encounters
    """)

def get_status_counts():
    return _fetch_all("SELECT status, COUNT(*) AS count FROM care_interventions GROUP BY status")

def get_risk_group_outcomes():
    """Per risk group: encounter count and historical <30 readmissions. `readmitted` is used here only AFTER scoring, for retrospective validation."""
    return _fetch_all("""
        SELECT risk_level, COUNT(*) AS encounters, COUNT(*) FILTER (WHERE readmitted = '<30') AS readmitted_under_30
        FROM patient_encounters GROUP BY risk_level
    """)

def count_pending_interventions():
    return _fetch_one("SELECT COUNT(*) AS count FROM care_interventions WHERE status = 'PENDING_REVIEW'")["count"]

# --- importer / setup helpers (take an open connection so the whole import is one transaction) ---
def count_rows(conn, table):
    """`table` must be one of the project's own tables, never user input."""
    if table not in ("patient_encounters", "care_interventions"): raise ValueError(f"Unknown table: {table}")
    return conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]

def upsert_encounters(conn, rows):
    columns = ENCOUNTER_COLUMNS
    updates = ", ".join(f"{column} = EXCLUDED.{column}" for column in columns if column != "encounter_id")
    query = f"INSERT INTO patient_encounters ({', '.join(columns)}) VALUES ({', '.join(f'%({c})s' for c in columns)}) ON CONFLICT (encounter_id) DO UPDATE SET {updates}"
    with conn.cursor() as cursor: cursor.executemany(query, rows)

def create_interventions(conn, encounter_ids):
    with conn.cursor() as cursor: cursor.executemany("INSERT INTO care_interventions (encounter_id) VALUES (%s) ON CONFLICT (encounter_id) DO NOTHING", [(encounter_id,) for encounter_id in encounter_ids])

def table_exists(conn, table):
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL AS found", (f"public.{table}",)).fetchone()["found"]
