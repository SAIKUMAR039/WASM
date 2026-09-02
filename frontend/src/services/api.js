const BASE_URL = 'http://localhost:8000/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };
  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${res.status}`);
    }
    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API call failed for ${endpoint}:`, err.message);
    throw err;
  }
}

export const api = {
  // Plugin Endpoints
  getPlugins: (tenantId = 'tenant_default') => request(`/plugins?tenant_id=${tenantId}`),
  createPlugin: (data) => request('/plugins', { method: 'POST', body: JSON.stringify(data) }),
  updatePlugin: (id, data) => request(`/plugins/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlugin: (id) => request(`/plugins/${id}`, { method: 'DELETE' }),

  // Execution Endpoint
  executeCode: (payload) => request('/execute', { method: 'POST', body: JSON.stringify(payload) }),

  // Metrics & Logs
  getMetricsSummary: (tenantId = 'tenant_default') => request(`/metrics/summary?tenant_id=${tenantId}`),
  getExecutions: (tenantId = 'tenant_default') => request(`/metrics/executions?tenant_id=${tenantId}`),

  // Security Settings
  getPolicy: (tenantId = 'tenant_default') => request(`/settings?tenant_id=${tenantId}`),
  updatePolicy: (policy) => request('/settings', { method: 'PUT', body: JSON.stringify(policy) }),
};
