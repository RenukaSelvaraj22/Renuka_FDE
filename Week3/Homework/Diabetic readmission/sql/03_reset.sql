-- Clears imported data (keeps tables and the status lookup). Both tables in one statement respects the foreign key.
TRUNCATE TABLE care_interventions, patient_encounters RESTART IDENTITY;
