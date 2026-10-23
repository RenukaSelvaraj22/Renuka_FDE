# Dataset

Place the diabetes hospital readmission CSV here as `data/diabetic_data.csv` (the "Diabetes 130-US hospitals" dataset provided for the assignment), or point `DATASET_PATH` in `.env` at wherever it lives.

CSV files are gitignored. The importer needs these columns: `encounter_id, patient_nbr, age, time_in_hospital, number_inpatient, number_emergency, number_outpatient, num_medications, num_lab_procedures, num_procedures, admission_type_id, discharge_disposition_id, readmitted`. Missing ones make the importer stop with a clear error.
