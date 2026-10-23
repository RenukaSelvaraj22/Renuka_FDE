from fastapi.testclient import TestClient

from app import main, service
from app.errors import DuplicateEncounterError
from app.main import app
from app.models import EncounterCreate

client = TestClient(app)

def test_service_calculates_risk_before_persisting(monkeypatch):
    saved = {}

    def save_encounter(encounter):
        saved.update(encounter)
        return encounter

    monkeypatch.setattr(service.repository, "create_encounter", save_encounter)
    payload = EncounterCreate(
        encounter_id=900001,
        patient_nbr=12345,
        number_inpatient=3,
        readmitted="NO",
    )

    result = service.create_encounter(payload)

    assert result["risk_score"] == 3
    assert result["risk_level"] == "MEDIUM"
    assert result["readmitted"] == "NO"
    assert saved == result


def test_create_encounter_returns_created_record(monkeypatch):
    created = {
        "encounter_id": 900001,
        "patient_nbr": 12345,
        "risk_score": 3,
        "risk_level": "MEDIUM",
        "review_reason": "3+ prior inpatient visits",
    }
    monkeypatch.setattr(main.service, "create_encounter", lambda _payload: created)

    response = client.post(
        "/encounters",
        json={"encounter_id": 900001, "patient_nbr": 12345, "number_inpatient": 3},
    )

    assert response.status_code == 201
    assert response.json() == created


def test_create_encounter_rejects_duplicate_id(monkeypatch):
    def raise_duplicate(_payload):
        raise DuplicateEncounterError("Encounter 900001 already exists")

    monkeypatch.setattr(main.service, "create_encounter", raise_duplicate)

    response = client.post(
        "/encounters",
        json={"encounter_id": 900001, "patient_nbr": 12345},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Encounter 900001 already exists"}


def test_create_encounter_validates_required_fields():
    response = client.post("/encounters", json={"patient_nbr": 12345})

    assert response.status_code == 422


def test_api_identifies_python_response_and_allows_local_typescript_origin():
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5500"},
    )

    assert response.status_code == 200
    assert response.headers["x-api-source"] == "python"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"
    assert "X-API-Source" in response.headers["access-control-expose-headers"]
