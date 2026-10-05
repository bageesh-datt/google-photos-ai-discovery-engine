const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api`
  : '/api';

export async function fetchPresetDataset() {
  const res = await fetch(`${API_BASE}/datasets/preset`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to load preset pilot dataset.');
  }
  return res.json();
}

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload custom CSV dataset.');
  }
  return res.json();
}

export async function startAnalysis(datasetId) {
  const res = await fetch(`${API_BASE}/analysis/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start AI analysis.');
  }
  return res.json();
}

export async function fetchAnalysisStatus(analysisId) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/status`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch pipeline status.');
  }
  return res.json();
}

export async function fetchObservations(analysisId, category = null) {
  let url = `${API_BASE}/analysis/${analysisId}/observations`;
  if (category) {
    url += `?category=${encodeURIComponent(category)}`;
  }
  const res = await fetch(url);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch observations.');
  }
  return res.json();
}

export async function fetchClusters(analysisId) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/clusters`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch clusters.');
  }
  return res.json();
}

export async function fetchOpportunities(analysisId) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/opportunities`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch opportunity areas.');
  }
  return res.json();
}

export async function fetchExportReport(analysisId) {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/export`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to generate export report.');
  }
  return res.json();
}
