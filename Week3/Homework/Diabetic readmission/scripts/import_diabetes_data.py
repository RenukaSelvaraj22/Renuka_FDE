"""Load the diabetes CSV into PostgreSQL, scoring each encounter and queueing MEDIUM/HIGH ones. Safe to rerun."""
import csv
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import repository, service
from app.config import get_dataset_path
from app.database import get_connection
from app.errors import AppError
BATCH_SIZE = 2000

def read_batches(path: Path):
    """Yield lists of parsed rows; validates the header first."""
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        service.validate_columns(reader.fieldnames)
        batch = []
        for line_number, row in enumerate(reader, start=2):
            batch.append(service.parse_encounter_row(row, line_number))
            if len(batch) == BATCH_SIZE: yield batch; batch = []
        if batch: yield batch

def import_dataset(path: Path) -> None:
    if not path.exists(): raise AppError(f"Dataset not found at {path}. Set DATASET_PATH in .env.")
    levels, rows_read = Counter(), 0
    with get_connection() as conn:
        required_tables = ("intervention_statuses", "patient_encounters", "care_interventions")
        missing_tables = [table for table in required_tables if not repository.table_exists(conn, table)]
        if missing_tables:
            raise AppError(
                "Database schema is incomplete. Run "
                "sql/01_create_schema.sql and sql/02_seed_intervention_statuses.sql "
                f"first; missing tables: {', '.join(missing_tables)}."
            )
        permissions = conn.execute("""
            SELECT has_schema_privilege(current_user, 'public', 'USAGE') AS schema_usage,
                   has_table_privilege(current_user, 'public.intervention_statuses', 'SELECT') AS statuses_select,
                   has_table_privilege(current_user, 'public.patient_encounters', 'SELECT') AS encounters_select,
                   has_table_privilege(current_user, 'public.patient_encounters', 'INSERT') AS encounters_insert,
                   has_table_privilege(current_user, 'public.patient_encounters', 'UPDATE') AS encounters_update,
                   has_table_privilege(current_user, 'public.care_interventions', 'SELECT') AS interventions_select,
                   has_table_privilege(current_user, 'public.care_interventions', 'INSERT') AS interventions_insert
        """).fetchone()
        required_permissions = {
            "USAGE on the public schema": permissions["schema_usage"],
            "SELECT on intervention_statuses": permissions["statuses_select"],
            "SELECT, INSERT, and UPDATE on patient_encounters": all((
                permissions["encounters_select"],
                permissions["encounters_insert"],
                permissions["encounters_update"],
            )),
            "SELECT and INSERT on care_interventions": all((
                permissions["interventions_select"],
                permissions["interventions_insert"],
            )),
        }
        missing_permissions = [name for name, granted in required_permissions.items() if not granted]
        if missing_permissions:
            raise AppError(
                "The database role lacks required permissions: "
                f"{', '.join(missing_permissions)}. Have the database owner grant "
                "these permissions to the role in DATABASE_URL, then retry."
            )
        pending_status = conn.execute(
            "SELECT 1 FROM intervention_statuses WHERE status = %s",
            ("PENDING_REVIEW",),
        ).fetchone()
        if pending_status is None:
            raise AppError(
                "Database statuses are not seeded. Run "
                "sql/02_seed_intervention_statuses.sql before importing."
            )
        encounters_before, queue_before = repository.count_rows(conn, "patient_encounters"), repository.count_rows(conn, "care_interventions")
        for batch in read_batches(path):
            repository.upsert_encounters(conn, batch)
            repository.create_interventions(conn, [row["encounter_id"] for row in batch if row["risk_level"] != "LOW"])
            rows_read += len(batch)
            levels.update(row["risk_level"] for row in batch)
        encounters_after, queue_after = repository.count_rows(conn, "patient_encounters"), repository.count_rows(conn, "care_interventions")
    inserted = encounters_after - encounters_before
    print(f"Import completed\n\nRows read:                 {rows_read}\nRows inserted:             {inserted}\nRows updated/skipped:      {rows_read - inserted}")
    print(f"LOW risk:                  {levels['LOW']}\nMEDIUM risk:               {levels['MEDIUM']}\nHIGH risk:                 {levels['HIGH']}")
    print(f"New care queue records:    {queue_after - queue_before}\nCare queue records (total): {queue_after}")

if __name__ == "__main__":
    try: import_dataset(get_dataset_path())
    except AppError as exc: sys.exit(f"Import failed: {exc}")
