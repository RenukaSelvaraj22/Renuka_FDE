-- Schema for the Diabetes Readmission Intervention Queue (educational prototype)
CREATE TABLE IF NOT EXISTS intervention_statuses (
    status VARCHAR(30) PRIMARY KEY,
    sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS patient_encounters (
    encounter_id BIGINT PRIMARY KEY,
    patient_nbr BIGINT NOT NULL,
    age VARCHAR(30),
    time_in_hospital INTEGER,
    number_inpatient INTEGER,
    number_emergency INTEGER,
    number_outpatient INTEGER,
    num_medications INTEGER,
    num_lab_procedures INTEGER,
    num_procedures INTEGER,
    admission_type_id INTEGER,
    discharge_disposition_id INTEGER,
    readmitted VARCHAR(10),  -- historical outcome: analysis only, never used for scoring
    risk_score INTEGER NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    review_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_risk_level CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH'))
);

CREATE INDEX IF NOT EXISTS idx_encounters_risk_level ON patient_encounters (risk_level);
CREATE INDEX IF NOT EXISTS idx_encounters_readmitted ON patient_encounters (readmitted);

CREATE TABLE IF NOT EXISTS care_interventions (
    intervention_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    encounter_id BIGINT NOT NULL UNIQUE REFERENCES patient_encounters (encounter_id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW' REFERENCES intervention_statuses (status),
    assigned_to VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_interventions_status ON care_interventions (status);
