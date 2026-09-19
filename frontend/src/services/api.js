import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Helper Endpoints
export const checkHealth = async () => {
  try {
    const res = await apiClient.get('/health');
    return { ok: true, data: res.data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
};

export const predictTicket = async (ticketPayload) => {
  const res = await apiClient.post('/api/v1/predict', ticketPayload);
  return res.data;
};

export const predictBatchTickets = async (ticketsArray) => {
  const res = await apiClient.post('/api/v1/predict/batch', { tickets: ticketsArray });
  return res.data;
};

export const getMonitoringMetrics = async () => {
  const res = await apiClient.get('/api/v1/monitoring/metrics');
  return res.data;
};

export const getPredictionLogs = async (limit = 100) => {
  const res = await apiClient.get(`/api/v1/monitoring/logs?limit=${limit}`);
  return res.data;
};

export const analyzeDrift = async (windowSize = 200) => {
  const res = await apiClient.post(`/api/v1/monitoring/drift/analyze?window_size=${windowSize}`);
  return res.data;
};

export const promoteModelVersion = async (version, alias = 'production') => {
  const res = await apiClient.post(`/api/v1/registry/promote?version=${version}&alias=${alias}`);
  return res.data;
};

export const rollbackModelVersion = async (targetVersion) => {
  const res = await apiClient.post(`/api/v1/registry/rollback?target_version=${targetVersion}`);
  return res.data;
};
