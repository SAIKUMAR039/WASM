const BASE_URL = 'http://localhost:8000/api';

let authToken = localStorage.getItem('wasmbox_auth_token') || null;
let currentTenant = localStorage.getItem('wasmbox_tenant_id') || 'tenant_default';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(currentTenant ? { 'X-Tenant-ID': currentTenant } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
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
  // Token & Session State
  setToken: (token) => {
    authToken = token;
    if (token) localStorage.setItem('wasmbox_auth_token', token);
    else localStorage.removeItem('wasmbox_auth_token');
  },
  getToken: () => authToken,
  setTenant: (tenantId) => {
    currentTenant = tenantId;
    if (tenantId) localStorage.setItem('wasmbox_tenant_id', tenantId);
    else localStorage.removeItem('wasmbox_tenant_id');
  },
  getTenant: () => currentTenant,

  // Authentication
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // Tenant & Organization
  getTenants: () => request('/tenants'),
  createTenant: (data) => request('/tenants', { method: 'POST', body: JSON.stringify(data) }),
  getTenantById: (id) => request(`/tenants/${id}`),

  // API Key Management
  getApiKeys: (tenantId = currentTenant) => request(`/tenants/${tenantId}/api-keys`),
  createApiKey: (tenantId, data) => request(`/tenants/${tenantId}/api-keys`, { method: 'POST', body: JSON.stringify(data) }),
  deleteApiKey: (tenantId, keyId) => request(`/tenants/${tenantId}/api-keys/${keyId}`, { method: 'DELETE' }),

  // Plugin Endpoints
  getPlugins: (tenantId = currentTenant) => request(`/plugins?tenant_id=${tenantId}`),
  createPlugin: (data) => request('/plugins', { method: 'POST', body: JSON.stringify(data) }),
  updatePlugin: (id, data) => request(`/plugins/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlugin: (id) => request(`/plugins/${id}`, { method: 'DELETE' }),

  // Execution Endpoint
  executeCode: (payload) => request('/execute', { method: 'POST', body: JSON.stringify(payload) }),

  // Metrics & Logs
  getMetricsSummary: (tenantId = currentTenant) => request(`/metrics/summary?tenant_id=${tenantId}`),
  getExecutions: (tenantId = currentTenant) => request(`/metrics/executions?tenant_id=${tenantId}`),

  // Security Settings
  getPolicy: (tenantId = currentTenant) => request(`/settings?tenant_id=${tenantId}`),
  updatePolicy: (policy) => request('/settings', { method: 'PUT', body: JSON.stringify(policy) }),
};
