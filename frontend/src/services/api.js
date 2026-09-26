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
  getPlugins: (tenantId = 'tenant_default', { category, tag, search } = {}) => {
    const params = new URLSearchParams({ tenant_id: tenantId });
    if (category) params.append('category', category);
    if (tag) params.append('tag', tag);
    if (search) params.append('search', search);
    return request(`/plugins?${params.toString()}`);
  },
  getTemplates: () => request('/plugins/templates'),
  validateCode: (code) => request('/plugins/validate', { method: 'POST', body: JSON.stringify({ code }) }),
  createPlugin: (data) => request('/plugins', { method: 'POST', body: JSON.stringify(data) }),
  updatePlugin: (id, data) => request(`/plugins/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlugin: (id) => request(`/plugins/${id}`, { method: 'DELETE' }),

  // Execution Endpoints
  executeCode: (payload) => request('/execute', { method: 'POST', body: JSON.stringify(payload) }),
  submitAsyncJob: (payload) => request('/execute/async', { method: 'POST', body: JSON.stringify(payload) }),
  getJobStatus: (jobId) => request(`/execute/jobs/${jobId}`),
  listJobs: (tenantId = 'tenant_default', limit = 50) => request(`/execute/jobs?tenant_id=${tenantId}&limit=${limit}`),
  runBenchmark: (payload) => request('/execute/benchmark', { method: 'POST', body: JSON.stringify(payload) }),
  inspectBytecode: (code) => request('/execute/inspect-bytecode', { method: 'POST', body: JSON.stringify({ code }) }),

  executeStream: (payload, { onChunk, onStatus, onResult, onError } = {}) => {
    return new Promise((resolve, reject) => {
      const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
      const wsProtocol = isHttps ? 'wss:' : 'ws:';
      const host = typeof window !== 'undefined' && window.location.hostname === 'localhost'
        ? 'localhost:8000'
        : (typeof window !== 'undefined' && window.location.host ? window.location.host : 'localhost:8000');
      const wsUrl = `${wsProtocol}//${host}/ws/execute`;

      let socket;
      let isSettled = false;
      let requestSent = false;

      try {
        socket = new WebSocket(wsUrl);
      } catch (err) {
        console.warn('WebSocket initialization failed, falling back to HTTP:', err);
        return api.executeCode(payload)
          .then((res) => {
            if (onResult) onResult(res);
            resolve(res);
          })
          .catch((e) => {
            if (onError) onError(e);
            reject(e);
          });
      }

      socket.onopen = () => {
        if (onStatus) onStatus('RUNNING');
        try {
          socket.send(JSON.stringify(payload));
          requestSent = true;
        } catch (err) {
          console.warn('Failed to send payload over WebSocket:', err);
        }
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'stdout' || msg.type === 'stderr') {
            if (onChunk) onChunk(msg.data, msg.type);
          } else if (msg.type === 'status') {
            if (onStatus) onStatus(msg.status);
          } else if (msg.type === 'result') {
            isSettled = true;
            if (onResult) onResult(msg);
            resolve(msg);
            try { socket.close(); } catch (e) {}
          } else if (msg.type === 'error') {
            isSettled = true;
            const err = new Error(msg.error || 'Execution failed');
            if (onError) onError(err);
            reject(err);
            try { socket.close(); } catch (e) {}
          }
        } catch (e) {
          if (onChunk) onChunk(event.data, 'stdout');
        }
      };

      socket.onerror = (err) => {
        if (!isSettled) {
          if (!requestSent) {
            console.warn('WebSocket stream error before request sent, fallback to REST execute:', err);
            api.executeCode(payload)
              .then((res) => {
                isSettled = true;
                if (onResult) onResult(res);
                resolve(res);
              })
              .catch((e) => {
                isSettled = true;
                if (onError) onError(e);
                reject(e);
              });
          } else {
            isSettled = true;
            const streamErr = new Error('WebSocket stream error during execution');
            if (onError) onError(streamErr);
            reject(streamErr);
          }
        }
      };

      socket.onclose = () => {
        if (!isSettled) {
          isSettled = true;
          if (onStatus) onStatus('DISCONNECTED');
          if (!requestSent) {
            console.warn('WebSocket closed before request sent, fallback to REST execute');
            api.executeCode(payload)
              .then((res) => {
                if (onResult) onResult(res);
                resolve(res);
              })
              .catch((e) => {
                if (onError) onError(e);
                reject(e);
              });
          } else {
            const closeErr = new Error('WebSocket connection closed unexpectedly before completion');
            if (onError) onError(closeErr);
            reject(closeErr);
          }
        }
      };
    });
  },

  // Metrics & Logs
  getMetricsSummary: (tenantId = 'tenant_default') => request(`/metrics/summary?tenant_id=${tenantId}`),
  getExecutions: (tenantId = 'tenant_default') => request(`/metrics/executions?tenant_id=${tenantId}`),
  getMetricsTrends: (tenantId = 'tenant_default', limit = 30) => request(`/metrics/trends?tenant_id=${tenantId}&limit=${limit}`),

  // Security Settings & Quota
  getPolicy: (tenantId = 'tenant_default') => request(`/settings?tenant_id=${tenantId}`),
  updatePolicy: (policy) => request('/settings', { method: 'PUT', body: JSON.stringify(policy) }),
  getQuota: (tenantId = 'tenant_default') => request(`/settings/quota?tenant_id=${tenantId}`),
};
