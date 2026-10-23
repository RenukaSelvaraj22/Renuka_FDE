export interface EncounterCreateRequest {
  encounter_id: number;
  patient_nbr: number;
  age?: string | null;
  time_in_hospital?: number | null;
  number_inpatient?: number | null;
  number_emergency?: number | null;
  number_outpatient?: number | null;
  num_medications?: number | null;
  num_lab_procedures?: number | null;
  num_procedures?: number | null;
  admission_type_id?: number | null;
  discharge_disposition_id?: number | null;
  readmitted?: '<30' | '>30' | 'NO' | null;
}

export interface EncounterResponse extends EncounterCreateRequest {
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  review_reason: string;
  created_at: string;
  intervention_id?: number | null;
  intervention_status?: 'PENDING_REVIEW' | 'ASSIGNED' | 'CONTACTED' | 'FOLLOW_UP_SCHEDULED' | 'CLOSED' | null;
}

export interface InterventionUpdateResponse {
  intervention_id: number;
  encounter_id: number;
  status: NonNullable<EncounterResponse['intervention_status']>;
  assigned_to: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

const API_URL = 'http://127.0.0.1:8001';

export async function createEncounter(
  encounter: EncounterCreateRequest,
): Promise<EncounterResponse> {
  const response = await fetch(`${API_URL}/encounters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(encounter),
  });

  const apiSource = response.headers.get('X-API-Source');
  if (apiSource !== 'python') {
    throw new Error(
      'Response was not confirmed as coming from the Python API. Check the API URL and CORS configuration.',
    );
  }

  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => undefined);
    throw new Error(
      `Python API returned ${response.status}: ${JSON.stringify(detail)}`,
    );
  }

  return (await response.json()) as EncounterResponse;
}

export async function fetchEncounterById(
  encounterId: number,
): Promise<EncounterResponse> {
  const response = await fetch(`${API_URL}/encounters/${encounterId}`);
  if (response.headers.get('X-API-Source') !== 'python') {
    throw new Error('Response was not confirmed as coming from the Python API.');
  }
  if (!response.ok) {
    throw new Error(`Python API returned ${response.status} for encounter ${encounterId}.`);
  }
  return (await response.json()) as EncounterResponse;
}

export async function listEncounters(
  limit = 50,
  offset = 0,
): Promise<EncounterResponse[]> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const response = await fetch(`${API_URL}/encounters?${query}`);
  if (response.headers.get('X-API-Source') !== 'python') {
    throw new Error('Response was not confirmed as coming from the Python API.');
  }
  if (!response.ok) {
    throw new Error(`Python API returned ${response.status} while listing encounters.`);
  }
  return (await response.json()) as EncounterResponse[];
}

export async function updateInterventionStatus(
  encounterId: number,
  status: NonNullable<EncounterResponse['intervention_status']>,
): Promise<InterventionUpdateResponse> {
  const response = await fetch(`${API_URL}/interventions/${encounterId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (response.headers.get('X-API-Source') !== 'python') {
    throw new Error('Response was not confirmed as coming from the Python API.');
  }
  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => undefined);
    throw new Error(
      `Python API returned ${response.status}: ${JSON.stringify(detail)}`,
    );
  }
  return (await response.json()) as InterventionUpdateResponse;
}