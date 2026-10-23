"""Check that the environment, database and tables are ready."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import repository
from app.config import get_database_url
from app.database import get_connection
from app.errors import AppError

def main() -> None:
    get_database_url()
    print("DATABASE_URL: OK")
    with get_connection() as conn:
        print("Database connection: OK")
        missing = [table for table in ("patient_encounters", "care_interventions") if not repository.table_exists(conn, table)]
        for table in ("patient_encounters", "care_interventions"): print(f"{table} table: {'MISSING' if table in missing else 'OK'}")
        if missing: sys.exit("\nSetup incomplete: run sql/01_create_schema.sql and sql/02_seed_intervention_statuses.sql")
        print(f"Encounter rows: {repository.count_rows(conn, 'patient_encounters')}\nCare queue rows: {repository.count_rows(conn, 'care_interventions')}")
    print("\nSetup verification successful.")

if __name__ == "__main__":
    try: main()
    except AppError as exc: sys.exit(f"Setup verification failed: {exc}")
