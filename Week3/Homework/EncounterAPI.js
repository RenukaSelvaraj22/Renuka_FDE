const API_URL = 'http://127.0.0.1:8001';
export async function createEncounter(encounter) {
    const response = await fetch(`${API_URL}/encounters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(encounter),
    });
    const apiSource = response.headers.get('X-API-Source');
    if (apiSource !== 'python') {
        throw new Error('Response was not confirmed as coming from the Python API. Check the API URL and CORS configuration.');
    }
    if (!response.ok) {
        const detail = await response.json().catch(() => undefined);
        throw new Error(`Python API returned ${response.status}: ${JSON.stringify(detail)}`);
    }
    return (await response.json());
}
export async function fetchEncounterById(encounterId) {
    const response = await fetch(`${API_URL}/encounters/${encounterId}`);
    if (response.headers.get('X-API-Source') !== 'python') {
        throw new Error('Response was not confirmed as coming from the Python API.');
    }
    if (!response.ok) {
        throw new Error(`Python API returned ${response.status} for encounter ${encounterId}.`);
    }
    return (await response.json());
}
export async function listEncounters(limit = 50, offset = 0) {
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
    return (await response.json());
}
export async function updateInterventionStatus(encounterId, status) {
    const response = await fetch(`${API_URL}/interventions/${encounterId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
    });
    if (response.headers.get('X-API-Source') !== 'python') {
        throw new Error('Response was not confirmed as coming from the Python API.');
    }
    if (!response.ok) {
        const detail = await response.json().catch(() => undefined);
        throw new Error(`Python API returned ${response.status}: ${JSON.stringify(detail)}`);
    }
    return (await response.json());
}
