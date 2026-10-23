# Diabetes Readmission Intervention Queue

Testleaf FDE Week 2 mini project: turn historical diabetes encounter data into an explainable, trackable care-management review queue.

> **Educational prototype only.** Not clinically validated, not for patient-care decisions. The risk rules are illustrative learning assumptions, and the historical `readmitted` outcome is never used in scoring.

## FDE framing

- **User:** care-management team
- **Decision:** which diabetes encounters should be prioritized for follow-up?
- **Outcome:** a manageable, explainable review queue built from historical encounter data, plus metrics to see whether the prioritization lines up with historical outcomes.

| What the dataset tells us | What we do NOT know | MVP hypothesis |
|---|---|---|
| Historical encounters | Which readmissions were preventable? | Prior utilization may help prioritize follow-up |
| Historical <30-day readmissions | Cost of a readmission? | Care-management capacity is limited |
| Prior healthcare utilization | Current discharge workflow? | A risk queue may beat reviewing everyone |
| Operational / treatment attributes | Cost of intervention? | Rules are acceptable for an explainable MVP |
| Historical outcome | Clinical validity of rules? | Outcomes can evaluate the rule after scoring |

Further unknowns: are the risk signals available before discharge? What is real intervention capacity? What is the reimbursement impact of readmissions? Are there fairness/bias concerns?

## Architecture

```
CSV Dataset -> scripts/import_diabetes_data.py -> app/service.py (risk) -> PostgreSQL
PostgreSQL <- app/repository.py <- app/service.py <- app/main.py (FastAPI) <- Swagger / care team
```

| Path | Responsibility |
|---|---|
| `app/main.py` | routes, HTTP status codes (no SQL, no scoring) |
| `app/models.py` | Pydantic request/response models and enums |
| `app/service.py` | risk scoring, CSV row cleaning, metric calculations (no SQL) |
| `app/repository.py` | all parameterized SQL |
| `app/database.py`, `app/config.py`, `app/errors.py` | connection, environment, error types |
| `sql/` | schema, status seed, reset |
| `scripts/` | importer and setup check |
| `tests/` | unit tests for risk rules, parsing and health |

## Risk rules (illustrative)

| Condition | Points |
|---|---|
| `number_inpatient >= 3` | +3 |
| `number_emergency >= 2` | +2 |
| `number_outpatient >= 3` | +1 |
| `time_in_hospital >= 7` | +1 |
| `num_medications >= 20` | +1 |

0-2 = LOW, 3-4 = MEDIUM, 5+ = HIGH. MEDIUM and HIGH encounters get a care intervention (`PENDING_REVIEW`) automatically; LOW ones do not.

## Data leakage note

`readmitted` is the historical outcome. If it fed the score, the model would "predict" what already happened and any validation would be meaningless. It is stored only so `/operations/readmission-analysis` and `/management/dashboard` can compare the already-assigned risk groups with the `<30` outcome. Differing rates do not prove the rules are clinically predictive.

## Setup

1. **PostgreSQL:** create a database and user, then run the schema:
   ```bash
   psql -U postgres -c "CREATE USER fde_user WITH PASSWORD 'YOUR_LOCAL_PASSWORD';"
   psql -U postgres -c "CREATE DATABASE fde_db OWNER fde_user;"
   psql -U fde_user -d fde_db -f sql/01_create_schema.sql
   psql -U fde_user -d fde_db -f sql/02_seed_intervention_statuses.sql
   ```
   If those tables already exist and are owned by `postgres`, grant the app role access (replace `fde_user` if `DATABASE_URL` uses a different role):
   ```sql
   GRANT USAGE ON SCHEMA public TO fde_user;
   GRANT SELECT ON intervention_statuses TO fde_user;
   GRANT SELECT, INSERT, UPDATE ON patient_encounters TO fde_user;
   GRANT SELECT, INSERT ON care_interventions TO fde_user;
   ```
   Run these statements while connected to the application database as its owner or a PostgreSQL administrator.
2. **Python** (macOS/Linux):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Windows (PowerShell): `py -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt`
3. **.env:** copy `.env.example` to `.env` and set the real password. `.env` is gitignored.
4. **Dataset:** put the CSV at `data/diabetic_data.csv` (see `data/README.md`) or change `DATASET_PATH`.
5. **Check and import:**
   ```bash
   python scripts/verify_setup.py
   python scripts/import_diabetes_data.py
   ```
   The importer is safe to rerun (upserts encounters, never duplicates interventions). To start over: `psql -U fde_user -d fde_db -f sql/03_reset.sql`.
6. **Build the browser client** from the backend project folder:
   ```powershell
   cd ..
   npx --yes --package typescript tsc EncounterAPI.ts --target ES2020 --module ES2020 --lib DOM,ES2020 --strict --outDir .
   ```
   This writes `EncounterAPI.js` into `Day5_HW`, which the HTML page imports.
   In the first PowerShell window, start the API from `Day5_HW`:
   ```powershell
   python -m uvicorn --app-dir Frontend PEmain:app --reload --port 8001
   ```
   In a second PowerShell window, start the static server from `Day5_HW`:
   ```bash
   python -m http.server 5500
   ```
   Open <http://127.0.0.1:5500/Frontend/Index.html>. The page has separate Add Patient Encounter, Search & Browse Encounters, and Intervention Care & Tracking tabs. The browse tab loads the first 50 encounters through `GET /encounters`; use Previous/Next to page through results or search by encounter ID with `GET /encounters/{encounter_id}`. Searching loads and displays the matching encounter's intervention ID and status; the paginated list marks intervention details as requiring an individual search. The tracking tab maps readmission outcomes to intervention statuses (`<30` -> `FOLLOW_UP_SCHEDULED`, `>30` -> `CONTACTED`, `NO` -> `CLOSED`) and updates an existing intervention through `PATCH /interventions/{encounter_id}`. The add-encounter form calls the compiled TypeScript client to POST a new encounter, then GET the created encounter and render it. The client checks the `X-API-Source: python` response header. The `PEmain.py` entrypoint loads the API on port 8001. Local frontend origins on ports 5173, 5174, and 5500 are allowed by CORS.
7. **Tests:** `pytest`

## Key APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | health check |
| GET | `/encounters` | list (`limit`, `offset`, `risk_level`, `readmitted`) |
| POST | `/encounters` | create an encounter; the API calculates its risk and queues MEDIUM/HIGH encounters |
| GET | `/encounters/{encounter_id}` | one encounter + intervention (404 if missing) |
| GET | `/care-queue` | MEDIUM + HIGH queue, HIGH first (`risk_level`, `status`, `assigned_to`, paging) |
| GET | `/care-queue/high` | HIGH only |
| PATCH | `/interventions/{encounter_id}` | update `status` / `assigned_to` / `notes` |
| GET | `/operations/summary` | counts by risk level and intervention status |
| GET | `/operations/readmission-analysis` | risk groups vs historical `<30` outcome |
| GET | `/management/dashboard` | executive summary |

Create an encounter with `POST /encounters` (send `encounter_id` and `patient_nbr`; other encounter attributes are optional):
```json
{
  "encounter_id": 900001,
  "patient_nbr": 12345,
  "number_inpatient": 3,
  "number_emergency": 0
}
```
Risk fields are calculated by the API, not accepted from the request. The endpoint returns `201 Created`, or `409 Conflict` if the encounter ID already exists.
The TypeScript client (`../EncounterAPI.ts`, relative to the `Frontend` directory) exports `createEncounter` and `fetchEncounterById`:
```typescript
import { createEncounter } from './EncounterAPI';

const created = await createEncounter({
  encounter_id: 900001,
  patient_nbr: 12345,
  number_inpatient: 3,
  readmitted: 'NO',
});
console.log(created.risk_level); // HIGH/MEDIUM/LOW calculated by the Python API
```

## Demo workflow

`verify_setup.py` -> import -> start API -> `GET /operations/summary` -> `GET /care-queue/high` -> pick an `encounter_id` -> `GET /encounters/{id}` -> `PATCH /interventions/{id}` (`CONTACTED`, `Care Team A`) -> `GET /care-queue?status=CONTACTED` -> `GET /operations/readmission-analysis` -> `GET /management/dashboard` -> restart the API -> fetch the same encounter -> the update is still there (it lives in PostgreSQL).

## FDE reflection (fill in after your run)

1. What business problem did you solve?
2. Who is the primary user?
3. What decision does your application improve?
4. What did the dataset prove? (use your own `/operations/readmission-analysis` numbers)
5. What assumptions did you make?
6. What must the hospital validate before this could become a real product?
7. Rules, traditional ML, LLM or something else next, and why?

## Stretch ideas (not implemented)

Filter by age range or prior inpatient count, intervention history table, care-team assignment, sort parameters, CSV export of the queue, alternate risk thresholds, richer retrospective metrics.
